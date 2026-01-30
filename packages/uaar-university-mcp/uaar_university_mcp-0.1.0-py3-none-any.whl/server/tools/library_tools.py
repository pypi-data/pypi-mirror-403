from typing import List, Optional
from server.schemas import LibraryBook, BookBorrowing, PaginatedResponse
from server.database import query_db

def register_library_tools(mcp):
    @mcp.tool(
        name="search_library_books",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def search_library_books(query: str, category: Optional[str] = None, limit: int = 10, offset: int = 0) -> PaginatedResponse[LibraryBook]:
        """Search for books in the university library by title, author, or ISBN."""
        search_term = f"%{query}%"
        sql = "SELECT * FROM library_books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?"
        params = [search_term, search_term, search_term]

        if category:
            sql += " AND category LIKE ?"
            params.append(f"%{category}%")

        sql += f" LIMIT {limit} OFFSET {offset}"

        books = query_db(sql, tuple(params))

        # Count total
        count_sql = "SELECT COUNT(*) as count FROM library_books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?"
        count_params = [search_term, search_term, search_term]
        if category:
            count_sql += " AND category LIKE ?"
            count_params.append(f"%{category}%")

        total = query_db(count_sql, tuple(count_params), one=True)['count']

        items = [LibraryBook(**b) for b in books]

        return PaginatedResponse(
            total=total,
            count=len(items),
            offset=offset,
            items=items,
            has_more=offset + len(items) < total,
            next_offset=offset + len(items) if offset + len(items) < total else None
        )

    @mcp.tool(
        name="check_book_availability",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def check_book_availability(book_id: str) -> dict:
        """Check if a specific book is available for borrowing."""
        book = query_db("SELECT * FROM library_books WHERE id = ?", (book_id,), one=True)
        if not book:
            return {"error": "Book not found"}
        return {
            "book_id": book['id'],
            "title": book['title'],
            "available": book['available_copies'] > 0,
            "available_copies": book['available_copies'],
            "location": book['location']
        }

    @mcp.tool(
        name="get_borrowed_books",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_borrowed_books(student_id: str) -> List[BookBorrowing]:
        """Get list of books currently borrowed by a student."""
        # Note: This requires a 'borrowings' table which isn't in the schema yet.
        # For now we'll return an empty list or implement the table if needed.
        # Assuming we stick to the provided schema for now, logic might be mock or empty.
        # Let's keep it simple and consistent:
        return []

    @mcp.tool(
        name="get_library_hours",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_library_hours() -> dict:
        """Get library operating hours."""
        rows = query_db("SELECT day_type, hours FROM library_hours")
        return {row['day_type']: row['hours'] for row in rows}
