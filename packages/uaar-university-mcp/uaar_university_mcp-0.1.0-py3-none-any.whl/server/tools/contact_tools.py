from typing import List, Optional
from server.schemas import DepartmentContact, HelpTicket
from server.database import execute_db, query_db

def register_contact_tools(mcp):
    @mcp.tool(
        name="get_department_contact",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_department_contact(department_name: Optional[str] = None) -> List[DepartmentContact]:
        """Get contact information for university departments. Optionally filter by name."""
        sql = "SELECT * FROM department_contacts"
        params = []
        if department_name:
            sql += " WHERE department LIKE ?"
            params.append(f"%{department_name}%")

        rows = query_db(sql, tuple(params))
        return [DepartmentContact(**r) for r in rows]

    @mcp.tool(
        name="get_emergency_contacts",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_emergency_contacts() -> dict:
        """Get emergency contact numbers for the university."""
        rows = query_db("SELECT key, number FROM emergency_contacts")
        return {row['key']: row['number'] for row in rows}

    @mcp.tool(
        name="submit_help_ticket",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def submit_help_ticket(student_id: str, category: str, subject: str, description: str) -> dict:
        """Submit a help ticket for IT or administrative issues."""
        # Generate ID
        count = query_db("SELECT COUNT(*) as c FROM help_tickets", one=True)['c']
        ticket_id = f"TKT{count + 1:04d}"

        import datetime
        created_at = datetime.datetime.utcnow().isoformat()

        execute_db(
            "INSERT INTO help_tickets (ticket_id, student_id, category, subject, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, student_id, category, subject, description, "Open", created_at)
        )

        return {
            "ticket_id": ticket_id,
            "status": "Submitted",
            "message": f"Your ticket has been submitted. Reference: {ticket_id}. Expected response within 24-48 hours."
        }

    @mcp.tool(
        name="get_university_info",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_university_info() -> dict:
        """Get general university information."""
        rows = query_db("SELECT key, value FROM university_info")
        return {row['key']: row['value'] for row in rows}

    @mcp.tool(
        name="get_important_links",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_important_links() -> dict:
        """Get important university website links."""
        rows = query_db("SELECT key, url FROM important_links")
        return {row['key']: row['url'] for row in rows}
