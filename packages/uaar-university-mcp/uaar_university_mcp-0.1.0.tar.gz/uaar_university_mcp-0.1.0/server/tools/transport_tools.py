from typing import List, Optional
import json
from datetime import time
from server.schemas import BusRoute, BusStop
from server.database import query_db

def register_transport_tools(mcp):
    @mcp.tool(
        name="get_bus_routes",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_bus_routes(route_name: Optional[str] = None) -> List[BusRoute]:
        """Get university bus routes. Optionally filter by route name."""
        sql = "SELECT * FROM bus_routes"
        params = []
        if route_name:
            sql += " WHERE route_name LIKE ?"
            params.append(f"%{route_name}%")

        rows = query_db(sql, tuple(params))
        routes = []
        for row in rows:
            row = dict(row)
            if isinstance(row.get('stops'), str):
                try:
                    row['stops'] = json.loads(row['stops'])
                except:
                    row['stops'] = []
            # Convert time strings back to time objects if needed by Pydantic model
            # Assuming sqlite stores as HH:MM:SS string, Pydantic might handle it if type is datetime.time
            # For robustness we let Pydantic parse the string.
            routes.append(BusRoute(**row))
        return routes

    @mcp.tool(
        name="find_bus_stop",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def find_bus_stop(location: str) -> List[BusStop]:
        """Find bus stops near a location."""
        # This requires a 'bus_stops' table which we didn't add explicitly,
        # but we can search 'stops' JSON in 'bus_routes'
        # Or mock it if we don't want to complicate schema further for MVP.
        # Let's search inside the routes' stops JSON strings.
        search_term = f"%{location}%"
        routes = query_db("SELECT * FROM bus_routes WHERE stops LIKE ?", (search_term,))

        stops = []
        for r in routes:
            r_dict = dict(r)
            try:
                stop_list = json.loads(r_dict.get('stops', '[]'))
                for stop in stop_list:
                    if location.lower() in stop.lower():
                        # Construct a BusStop object from the route info
                        stops.append(BusStop(
                            stop_id=f"S-{r_dict['route_id']}",
                            name=stop,
                            routes=[r_dict['route_id']],
                            pickup_time=time(7, 0) # Mock time as we don't store per-stop time
                        ))
            except: pass
        return stops

    @mcp.tool(
        name="get_transport_card_info",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_transport_card_info() -> dict:
        """Get information about university transport card."""
        rows = query_db("SELECT key, value FROM transport_info")
        return {row['key']: row['value'] for row in rows}

    @mcp.tool(
        name="get_route_by_stop",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_route_by_stop(stop_name: str) -> List[BusRoute]:
        """Find all bus routes that pass through a specific stop."""
        search_term = f"%{stop_name}%"
        rows = query_db("SELECT * FROM bus_routes WHERE stops LIKE ?", (search_term,))
        routes = []
        for row in rows:
            row = dict(row)
            if isinstance(row.get('stops'), str):
                try:
                    row['stops'] = json.loads(row['stops'])
                except: row['stops'] = []
            routes.append(BusRoute(**row))
        return routes
