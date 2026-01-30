from server.schemas import UserProfile
from server.database import query_db

def register_user_tools(mcp):
    @mcp.tool(
        name="get_user_profile",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_user_profile(user_id: str) -> UserProfile:
        """Get profile information for a university member."""
        user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Map DB fields to schema if needed, but names match
        return UserProfile(
            id=user['id'],
            name=user['name'],
            email=user['email'],
            role=user['role'],
            department=user['department']
        )
