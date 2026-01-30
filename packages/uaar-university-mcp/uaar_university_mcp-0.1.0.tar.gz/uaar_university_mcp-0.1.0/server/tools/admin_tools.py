from typing import List, Dict, Any, Optional
import json
from server.database import execute_db, query_db

def register_admin_tools(mcp):
    @mcp.tool(
        name="admin_add_department",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_department(id: str, name: str, faculty: str, description: Optional[str] = None) -> str:
        """[Admin] Add a new academic department to the database."""
        try:
            execute_db(
                "INSERT INTO departments (id, name, faculty, description) VALUES (?, ?, ?, ?)",
                (id, name, faculty, description)
            )
            return f"Department '{name}' added successfully."
        except Exception as e:
            return f"Error adding department: {str(e)}"

    @mcp.tool(
        name="admin_add_course",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_course(code: str, title: str, department_id: str, credit_hours: int, description: Optional[str] = None) -> str:
        """[Admin] Add a new course."""
        try:
            execute_db(
                "INSERT INTO courses (code, title, department_id, credit_hours, description) VALUES (?, ?, ?, ?, ?)",
                (code, title, department_id, credit_hours, description)
            )
            return f"Course '{title}' added successfully."
        except Exception as e:
            return f"Error adding course: {str(e)}"

    @mcp.tool(
        name="admin_add_faculty",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_faculty(id: str, name: str, designation: str, department: str, email: str, research_interests: List[str]) -> str:
        """[Admin] Add a new faculty member."""
        try:
            execute_db(
                "INSERT INTO faculty (id, name, designation, department, email, research_interests) VALUES (?, ?, ?, ?, ?, ?)",
                (id, name, designation, department, email, json.dumps(research_interests))
            )
            return f"Faculty member '{name}' added successfully."
        except Exception as e:
            return f"Error adding faculty: {str(e)}"

    @mcp.tool(
        name="admin_add_event",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_event(id: str, title: str, date: str, location: str, description: str) -> str:
        """[Admin] Add a new university event (Date format: YYYY-MM-DD HH:MM:SS)."""
        try:
            execute_db(
                "INSERT INTO events (id, title, date, location, description) VALUES (?, ?, ?, ?, ?)",
                (id, title, date, location, description)
            )
            return f"Event '{title}' added successfully."
        except Exception as e:
            return f"Error adding event: {str(e)}"

    @mcp.tool(
        name="admin_add_news",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_news(id: str, title: str, date: str, content: str, category: str) -> str:
        """[Admin] Add a news item."""
        try:
            execute_db(
                "INSERT INTO news (id, title, date, content, category) VALUES (?, ?, ?, ?, ?)",
                (id, title, date, content, category)
            )
            return f"News '{title}' added successfully."
        except Exception as e:
            return f"Error adding news: {str(e)}"

    @mcp.tool(
        name="admin_add_book",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_book(id: str, title: str, author: str, isbn: str, category: str, total_copies: int, location: str) -> str:
        """[Admin] Add a library book."""
        try:
            execute_db(
                "INSERT INTO library_books (id, title, author, isbn, category, available_copies, total_copies, location) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id, title, author, isbn, category, total_copies, total_copies, location)
            )
            return f"Book '{title}' added successfully."
        except Exception as e:
            return f"Error adding book: {str(e)}"

    @mcp.tool(
        name="admin_add_scholarship",
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    )
    async def admin_add_scholarship(id: str, name: str, provider: str, amount: float, duration: str, eligibility: List[str], deadline: str, how_to_apply: str) -> str:
        """[Admin] Add a scholarship opportunity."""
        try:
            execute_db(
                "INSERT INTO scholarships (id, name, provider, amount, duration, eligibility, deadline, how_to_apply) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id, name, provider, amount, duration, json.dumps(eligibility), deadline, how_to_apply)
            )
            return f"Scholarship '{name}' added successfully."
        except Exception as e:
            return f"Error adding scholarship: {str(e)}"
