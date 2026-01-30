from typing import Optional, List, Dict
import json
from datetime import datetime
from server.schemas import AdmissionForm, AdmissionFormDraft
from server.database import execute_db, query_db

REQUIRED_FIELDS = [
    "full_name", "father_name", "cnic", "date_of_birth", "gender",
    "email", "phone", "address", "city", "province", "domicile",
    "matric_board", "matric_year", "matric_marks_obtained", "matric_total_marks",
    "inter_board", "inter_year", "inter_marks_obtained", "inter_total_marks",
    "program_choice_1"
]

def _generate_application_id():
    # Count existing forms to generate ID
    count = query_db("SELECT COUNT(*) as c FROM admission_forms", one=True)['c']
    return f"APP-2026-{count + 1:05d}"

def _calculate_percentage(obtained: int, total: int) -> float:
    return round((obtained / total) * 100, 2) if total > 0 else 0.0

def _calculate_aggregate(matric_pct: float, inter_pct: float) -> float:
    return round((matric_pct * 0.10) + (inter_pct * 0.40) + 50, 2)

def _get_form(app_id):
    row = query_db("SELECT * FROM admission_forms WHERE application_id = ?", (app_id,), one=True)
    if not row:
        return None
    data = json.loads(row['data'])
    # Merge status/submitted_at back into data for convenience if needed,
    # but tools expect separate structure mostly.
    # The 'data' column stores the 'collected_fields' and metadata.
    return {
        "application_id": row['application_id'],
        "status": row['status'],
        "submitted_at": row['submitted_at'],
        **data
    }

def _save_form(app_id, data, status, submitted_at=None):
    # Check if exists
    exists = query_db("SELECT 1 FROM admission_forms WHERE application_id = ?", (app_id,), one=True)
    json_data = json.dumps(data)
    if exists:
        execute_db(
            "UPDATE admission_forms SET data = ?, status = ?, submitted_at = ? WHERE application_id = ?",
            (json_data, status, submitted_at, app_id)
        )
    else:
        execute_db(
            "INSERT INTO admission_forms (application_id, data, status, submitted_at) VALUES (?, ?, ?, ?)",
            (app_id, json_data, status, submitted_at)
        )

def register_admission_form_tools(mcp):

    @mcp.tool(
        name="start_admission_form",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def start_admission_form() -> dict:
        """Start a new admission form application. Returns application ID and list of required fields."""
        app_id = _generate_application_id()

        form_data = {
            "application_id": app_id,
            "collected_fields": {},
            "missing_fields": REQUIRED_FIELDS.copy(),
            "created_at": datetime.utcnow().isoformat()
        }

        _save_form(app_id, form_data, "Incomplete")

        # Fetch programs for convenience
        programs_rows = query_db("SELECT code, name FROM admission_programs")
        programs_list = [f"{row['code']} - {row['name']}" for row in programs_rows]

        return {
            "application_id": app_id,
            "message": "Admission form started. Please provide the required information.",
            "required_fields": REQUIRED_FIELDS,
            "available_programs": programs_list
        }

    @mcp.tool(
        name="fill_admission_field",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def fill_admission_field(application_id: str, field_name: str, field_value: str) -> dict:
        """Fill a single field in the admission form. Use this to collect information step by step."""
        form = _get_form(application_id)
        if not form:
            return {"error": "Application not found. Please start a new form first."}

        if form['status'] == "Submitted":
             return {"error": "Application already submitted."}

        if field_name not in REQUIRED_FIELDS and field_name not in ["program_choice_2", "program_choice_3", "hostel_required", "transport_required"]:
            return {"error": f"Unknown field: {field_name}"}

        # Value conversions
        if field_name in ["matric_year", "inter_year", "matric_marks_obtained", "matric_total_marks", "inter_marks_obtained", "inter_total_marks"]:
            try:
                field_value = int(field_value)
            except ValueError:
                return {"error": f"{field_name} must be a number"}

        if field_name in ["hostel_required", "transport_required"]:
            field_value = str(field_value).lower() in ["yes", "true", "1"]

        # Update data
        form["collected_fields"][field_name] = field_value

        if field_name in form["missing_fields"]:
            form["missing_fields"].remove(field_name)

        # Auto calculations
        if "matric_marks_obtained" in form["collected_fields"] and "matric_total_marks" in form["collected_fields"]:
            form["collected_fields"]["matric_percentage"] = _calculate_percentage(
                form["collected_fields"]["matric_marks_obtained"],
                form["collected_fields"]["matric_total_marks"]
            )

        if "inter_marks_obtained" in form["collected_fields"] and "inter_total_marks" in form["collected_fields"]:
            form["collected_fields"]["inter_percentage"] = _calculate_percentage(
                form["collected_fields"]["inter_marks_obtained"],
                form["collected_fields"]["inter_total_marks"]
            )

        if not form["missing_fields"]:
            form["status"] = "Ready for Review"
        else:
            form["status"] = "Incomplete" # Ensure status stays incomplete if fields missing

        # Save back to DB
        # We need to strip out top-level keys that are DB columns to avoid duplication in JSON if we want cleanest data,
        # but _save_form takes the whole dict as 'data'.
        # Ideally 'data' column should only store the variable form data.
        data_to_save = {
            "collected_fields": form["collected_fields"],
            "missing_fields": form["missing_fields"],
            "created_at": form.get("created_at")
        }
        _save_form(application_id, data_to_save, form["status"])

        return {
            "application_id": application_id,
            "field_updated": field_name,
            "status": form["status"],
            "missing_fields": form["missing_fields"],
            "fields_collected": len(form["collected_fields"]),
            "total_required": len(REQUIRED_FIELDS)
        }

    @mcp.tool(
        name="fill_multiple_admission_fields",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def fill_multiple_admission_fields(application_id: str, fields: Dict[str, str]) -> dict:
        """Fill multiple fields at once. Input: {'field_name': 'value', ...}"""
        form = _get_form(application_id)
        if not form:
            return {"error": "Application not found."}

        results = []
        for field_name, field_value in fields.items():
            result = await fill_admission_field(application_id, field_name, str(field_value))
            if "error" in result:
                results.append({field_name: result["error"]})
            else:
                results.append({field_name: "updated"})

        # Re-fetch to get final state
        draft = _get_form(application_id)
        return {
            "application_id": application_id,
            "updates": results,
            "status": draft["status"],
            "missing_fields": draft["missing_fields"]
        }

    @mcp.tool(
        name="get_admission_form_status",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_admission_form_status(application_id: str) -> dict:
        """Get current status of an admission form including collected and missing fields."""
        form = _get_form(application_id)
        if not form:
            return {"error": "Application not found"}

        if form['status'] == 'Submitted':
             return {
                "application_id": application_id,
                "status": "Submitted",
                "message": "Form has been submitted",
                "submitted_at": form.get("submitted_at")
            }

        return {
            "application_id": application_id,
            "status": form["status"],
            "collected_fields": form.get("collected_fields", {}),
            "missing_fields": form.get("missing_fields", []),
            "completion_percentage": round((len(REQUIRED_FIELDS) - len(form.get("missing_fields", []))) / len(REQUIRED_FIELDS) * 100, 1)
        }

    @mcp.tool(
        name="preview_admission_form",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def preview_admission_form(application_id: str) -> dict:
        """Preview the filled admission form before submission. Shows all collected data for approval."""
        form = _get_form(application_id)
        if not form:
            return {"error": "Application not found"}

        if form.get("missing_fields"):
            return {
                "error": "Form is incomplete",
                "missing_fields": form["missing_fields"],
                "message": "Please fill all required fields before preview"
            }

        fields = form["collected_fields"]
        aggregate = _calculate_aggregate(
            fields.get("matric_percentage", 0),
            fields.get("inter_percentage", 0)
        )

        return {
            "application_id": application_id,
            "status": "Ready for Review",
            "form_data": {
                "personal_info": {
                    "full_name": fields.get("full_name"),
                    "father_name": fields.get("father_name"),
                    "cnic": fields.get("cnic"),
                    "date_of_birth": fields.get("date_of_birth"),
                    "gender": fields.get("gender"),
                    "email": fields.get("email"),
                    "phone": fields.get("phone")
                },
                "address_info": {
                    "address": fields.get("address"),
                    "city": fields.get("city"),
                    "province": fields.get("province"),
                    "domicile": fields.get("domicile")
                },
                "matric_info": {
                    "board": fields.get("matric_board"),
                    "year": fields.get("matric_year"),
                    "marks": f"{fields.get('matric_marks_obtained')}/{fields.get('matric_total_marks')}",
                    "percentage": fields.get("matric_percentage")
                },
                "inter_info": {
                    "board": fields.get("inter_board"),
                    "year": fields.get("inter_year"),
                    "marks": f"{fields.get('inter_marks_obtained')}/{fields.get('inter_total_marks')}",
                    "percentage": fields.get("inter_percentage")
                },
                "program_choices": {
                    "first_choice": fields.get("program_choice_1"),
                    "second_choice": fields.get("program_choice_2", "Not selected"),
                    "third_choice": fields.get("program_choice_3", "Not selected")
                },
                "facilities": {
                    "hostel_required": fields.get("hostel_required", False),
                    "transport_required": fields.get("transport_required", False)
                },
                "calculated_aggregate": aggregate
            },
            "message": "Please review the above information. Call 'confirm_and_submit_admission_form' to submit or 'fill_admission_field' to make corrections."
        }

    @mcp.tool(
        name="confirm_and_submit_admission_form",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def confirm_and_submit_admission_form(application_id: str, confirmed: bool) -> dict:
        """Submit the admission form after user confirmation. Set confirmed=True to submit."""
        form = _get_form(application_id)
        if not form:
            return {"error": "Application not found"}

        if form['status'] == "Submitted":
             return {"error": "Application already submitted."}

        if not confirmed:
            return {
                "application_id": application_id,
                "status": "Not Submitted",
                "message": "Submission cancelled. You can continue editing the form or preview again."
            }

        if form.get("missing_fields"):
            return {
                "error": "Cannot submit incomplete form",
                "missing_fields": form["missing_fields"]
            }

        fields = form["collected_fields"]
        submitted_at = datetime.utcnow().isoformat()

        aggregate = _calculate_aggregate(
            fields.get("matric_percentage", 0),
            fields.get("inter_percentage", 0)
        )
        fields["aggregate_score"] = aggregate
        fields["application_id"] = application_id # Ensure it's in the data blob

        # Save as submitted
        data_to_save = {
            "collected_fields": fields,
            "missing_fields": [],
            "created_at": form.get("created_at"),
            "aggregate_score": aggregate
        }

        _save_form(application_id, data_to_save, "Submitted", submitted_at)

        return {
            "application_id": application_id,
            "status": "Submitted Successfully",
            "aggregate_score": aggregate,
            "message": f"Your admission form has been submitted successfully. Your application ID is {application_id}. Please save this for future reference.",
            "next_steps": [
                "Pay admission processing fee (Rs. 2000) at any HBL branch",
                "Upload fee challan at admission portal",
                "Wait for merit list announcement",
                "Check admission status using your CNIC"
            ]
        }

    @mcp.tool(
        name="get_available_programs",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_available_programs() -> List[dict]:
        """Get list of available programs for admission."""
        rows = query_db("SELECT * FROM admission_programs")
        return [dict(row) for row in rows]

    @mcp.tool(
        name="get_admission_requirements",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_admission_requirements() -> dict:
        """Get admission requirements and eligibility criteria."""
        rows = query_db("SELECT key, value FROM admission_requirements")
        result = {}
        for row in rows:
            try:
                result[row['key']] = json.loads(row['value'])
            except:
                result[row['key']] = row['value']
        return result
