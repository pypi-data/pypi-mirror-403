from typing import List
import json
from server.schemas import FacultyMember, PaginatedResponse
from server.database import query_db

def register_faculty_tools(mcp):
    @mcp.tool(
        name="search_faculty",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def search_faculty(query: str, limit: int = 10, offset: int = 0) -> PaginatedResponse[FacultyMember]:
        """Search for faculty members by name or research interest."""
        search_term = f"%{query}%"
        # We search by name or designation first
        faculty_rows = query_db(
            f"SELECT * FROM faculty WHERE name LIKE ? OR designation LIKE ? OR research_interests LIKE ? LIMIT {limit} OFFSET {offset}",
            (search_term, search_term, search_term)
        )
        total = query_db(
            "SELECT COUNT(*) as count FROM faculty WHERE name LIKE ? OR designation LIKE ? OR research_interests LIKE ?",
            (search_term, search_term, search_term),
            one=True
        )['count']

        items = []
        for row in faculty_rows:
            # Parse JSON string back to list
            row = dict(row)
            if isinstance(row.get('research_interests'), str):
                try:
                    row['research_interests'] = json.loads(row['research_interests'])
                except:
                    row['research_interests'] = []
            items.append(FacultyMember(**row))

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )
