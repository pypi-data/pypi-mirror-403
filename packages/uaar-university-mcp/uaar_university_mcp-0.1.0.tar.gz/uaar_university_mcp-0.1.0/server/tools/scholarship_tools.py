from typing import List, Optional
import json
from server.schemas import Scholarship, PaginatedResponse
from server.database import query_db

def register_scholarship_tools(mcp):
    @mcp.tool(
        name="list_scholarships",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def list_scholarships(provider: Optional[str] = None, limit: int = 10, offset: int = 0) -> PaginatedResponse[Scholarship]:
        """List available scholarships. Optionally filter by provider."""
        sql = "SELECT * FROM scholarships"
        params = []
        if provider:
            sql += " WHERE provider LIKE ?"
            params.append(f"%{provider}%")

        # Get total count first
        count_sql = f"SELECT COUNT(*) as count FROM ({sql})"
        total = query_db(count_sql, tuple(params), one=True)['count']

        # Apply pagination
        sql += f" LIMIT {limit} OFFSET {offset}"
        rows = query_db(sql, tuple(params))

        items = []
        for row in rows:
            row = dict(row)
            if isinstance(row.get('eligibility'), str):
                try:
                    row['eligibility'] = json.loads(row['eligibility'])
                except:
                    row['eligibility'] = []
            items.append(Scholarship(**row))

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )

    @mcp.tool(
        name="check_scholarship_eligibility",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def check_scholarship_eligibility(cgpa: float, family_income: int, is_punjab_domicile: bool = False) -> List[dict]:
        """Check which scholarships a student may be eligible for based on criteria."""
        rows = query_db("SELECT * FROM scholarships")
        eligible = []

        for row in rows:
            row = dict(row)
            try:
                eligibility = json.loads(row['eligibility']) if isinstance(row['eligibility'], str) else []
            except:
                eligibility = []

            reasons = []
            # Note: This logic is simple string matching, ideal for MVP
            for criteria in eligibility:
                if "CGPA" in criteria and ">=" in criteria:
                    try:
                        req_cgpa = float(criteria.split(">=")[1].strip())
                        if cgpa >= req_cgpa:
                            reasons.append("Meets CGPA requirement")
                    except: pass
                if "income" in criteria and "<" in criteria:
                    try:
                        # Extract number
                        import re
                        nums = re.findall(r'\d+', criteria.replace(',', ''))
                        if nums:
                            limit = int(nums[0])
                            if family_income < limit:
                                reasons.append("Meets income requirement")
                    except: pass
                if "Punjab domicile" in criteria and is_punjab_domicile:
                    reasons.append("Has Punjab domicile")

            if reasons:
                eligible.append({
                    "scholarship": row['name'],
                    "amount": row['amount'],
                    "reasons": reasons,
                    "deadline": row['deadline']
                })
        return eligible

    @mcp.tool(
        name="get_scholarship_details",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_scholarship_details(scholarship_id: str) -> Optional[Scholarship]:
        """Get detailed information about a specific scholarship."""
        row = query_db("SELECT * FROM scholarships WHERE id = ?", (scholarship_id,), one=True)
        if not row:
            return None
        row = dict(row)
        if isinstance(row.get('eligibility'), str):
            try:
                row['eligibility'] = json.loads(row['eligibility'])
            except:
                row['eligibility'] = []
        return Scholarship(**row)

    @mcp.tool(
        name="get_financial_aid_office_info",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_financial_aid_office_info() -> dict:
        """Get contact information for the Financial Aid Office."""
        return {
            "location": "Admin Block, Room 15",
            "hours": "9:00 AM - 4:00 PM (Mon-Fri)",
            "email": "financialaid@uaar.edu.pk",
            "phone": "051-9290000 Ext. 215",
            "documents_required": ["CNIC copy", "Income certificate", "Domicile", "Previous semester result"]
        }
