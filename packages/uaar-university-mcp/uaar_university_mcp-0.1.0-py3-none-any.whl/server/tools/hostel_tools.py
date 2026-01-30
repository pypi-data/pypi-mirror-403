from typing import List, Optional
from server.schemas import HostelRoom, MessMenu
from server.database import query_db

def register_hostel_tools(mcp):
    @mcp.tool(
        name="check_hostel_availability",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def check_hostel_availability(hostel_name: Optional[str] = None, room_type: Optional[str] = None) -> List[HostelRoom]:
        """Check available hostel rooms. Filter by hostel name or room type."""
        sql = "SELECT * FROM hostel_rooms WHERE available = 1"
        params = []
        if hostel_name:
            sql += " AND hostel_name LIKE ?"
            params.append(f"%{hostel_name}%")
        if room_type:
            sql += " AND room_type LIKE ?"
            params.append(f"%{room_type}%")

        rooms = query_db(sql, tuple(params))
        return [HostelRoom(**r) for r in rooms]

    @mcp.tool(
        name="get_mess_menu",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_mess_menu(day: Optional[str] = None) -> List[MessMenu]:
        """Get hostel mess menu. Optionally filter by day."""
        sql = "SELECT * FROM mess_menu"
        params = []
        if day:
            sql += " WHERE day LIKE ?"
            params.append(f"%{day}%")

        menus = query_db(sql, tuple(params))
        return [MessMenu(**m) for m in menus]

    @mcp.tool(
        name="get_hostel_fees",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_hostel_fees() -> dict:
        """Get hostel fee structure."""
        rows = query_db("SELECT * FROM hostel_fees")
        fees = {row['room_type']: {"monthly": row['monthly_rent'], "semester": row['semester_fee'], "security_deposit": row['security_deposit']} for row in rows}
        fees["note"] = "Fees are subject to change. Security deposit is refundable."
        return fees

    @mcp.tool(
        name="get_hostel_rules",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_hostel_rules() -> List[str]:
        """Get hostel rules and regulations."""
        rows = query_db("SELECT rule FROM hostel_rules")
        return [row['rule'] for row in rows]
