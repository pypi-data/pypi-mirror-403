from typing import List
from server.schemas import NewsItem, PaginatedResponse
from server.database import query_db

def register_news_tools(mcp):
    @mcp.tool(
        name="get_latest_news",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_latest_news(limit: int = 5, offset: int = 0) -> PaginatedResponse[NewsItem]:
        """Get the latest news and announcements."""
        news_items = query_db(f"SELECT * FROM news ORDER BY date DESC LIMIT {limit} OFFSET {offset}")
        total = query_db("SELECT COUNT(*) as count FROM news", one=True)['count']

        items = [NewsItem(**n) for n in news_items]

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )
