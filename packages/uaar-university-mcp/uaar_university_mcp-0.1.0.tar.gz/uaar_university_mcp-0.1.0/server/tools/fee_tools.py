from typing import Optional
from server.schemas import FeeInfo
from server.database import query_db

def register_fee_tools(mcp):
    @mcp.tool(
        name="get_fee_structure",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_fee_structure(program: str) -> Optional[FeeInfo]:
        """Get fee details for a specific academic program."""
        fee = query_db("SELECT * FROM fees WHERE program LIKE ?", (f"%{program}%",), one=True)
        if not fee:
            return None
        return FeeInfo(**fee)
