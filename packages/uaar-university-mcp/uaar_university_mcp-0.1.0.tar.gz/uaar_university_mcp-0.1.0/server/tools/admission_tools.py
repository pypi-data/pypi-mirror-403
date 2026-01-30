from typing import List
from server.schemas import MeritListItem, AdmissionStatus
from server.database import query_db

def register_admission_tools(mcp):
    @mcp.tool(
        name="get_merit_list",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_merit_list(dept_id: str) -> List[MeritListItem]:
        """Get the latest merit list for a department (Spring 2026)."""
        rows = query_db("SELECT * FROM merit_lists WHERE department_id = ? ORDER BY rank ASC", (dept_id,))
        return [MeritListItem(
            rank=r['rank'],
            student_name=r['student_name'],
            cnic_last_4=r['cnic_last_4'],
            aggregate_score=r['aggregate_score'],
            status=r['status']
        ) for r in rows]

    @mcp.tool(
        name="check_admission_status",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def check_admission_status(cnic: str) -> AdmissionStatus:
        """Check admission status using CNIC."""
        # First check if admitted in merit lists
        admitted = query_db("SELECT * FROM merit_lists WHERE cnic_last_4 = ?", (cnic[-4:],), one=True)

        if admitted:
            return AdmissionStatus(
                cnic=cnic,
                is_admitted=True,
                merit_rank=admitted['rank'],
                department=admitted['department_id'], # Ideally join with departments to get name, but ID works
                message=f"Selected in {admitted['department_id']} (Rank {admitted['rank']})"
            )

        # Check submitted forms status if not in merit list (requires joining/checking forms table)
        # We can simulate checking the forms table
        form = query_db("SELECT status FROM admission_forms WHERE data LIKE ?", (f'%"{cnic}"%',), one=True)

        if form:
            return AdmissionStatus(
                cnic=cnic,
                is_admitted=False,
                message=f"Application status: {form['status']}"
            )

        return AdmissionStatus(cnic=cnic, is_admitted=False, message="No application found or under review")
