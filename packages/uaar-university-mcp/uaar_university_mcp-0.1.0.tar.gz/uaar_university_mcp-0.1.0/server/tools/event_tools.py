from typing import List
from datetime import datetime
from server.schemas import Event, PaginatedResponse
from server.database import query_db

def register_event_tools(mcp):
    @mcp.tool(
        name="list_upcoming_events",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def list_upcoming_events(limit: int = 10, offset: int = 0) -> PaginatedResponse[Event]:
        """List upcoming university events and workshops."""
        # Simple query, practically you might filter by date >= current_date
        events = query_db(f"SELECT * FROM events ORDER BY date ASC LIMIT {limit} OFFSET {offset}")
        total = query_db("SELECT COUNT(*) as count FROM events", one=True)['count']

        items = [Event(**e) for e in events]

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )
