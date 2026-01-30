from typing import List, Optional
from server.schemas import Department, Course, PaginatedResponse
from server.database import query_db

def register_academic_tools(mcp):
    @mcp.tool(
        name="list_departments",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def list_departments(limit: int = 10, offset: int = 0) -> PaginatedResponse[Department]:
        """List all academic departments."""
        departments = query_db(f"SELECT * FROM departments LIMIT {limit} OFFSET {offset}")
        total = query_db("SELECT COUNT(*) as count FROM departments", one=True)['count']

        items = [Department(**d) for d in departments]

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )

    @mcp.tool(
        name="search_courses",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def search_courses(query: str, limit: int = 10, offset: int = 0) -> PaginatedResponse[Course]:
        """Search for courses by name or code."""
        search_term = f"%{query}%"
        courses = query_db(
            f"SELECT * FROM courses WHERE title LIKE ? OR code LIKE ? LIMIT {limit} OFFSET {offset}",
            (search_term, search_term)
        )
        total = query_db(
            "SELECT COUNT(*) as count FROM courses WHERE title LIKE ? OR code LIKE ?",
            (search_term, search_term),
            one=True
        )['count']

        items = [Course(**c) for c in courses]

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )
