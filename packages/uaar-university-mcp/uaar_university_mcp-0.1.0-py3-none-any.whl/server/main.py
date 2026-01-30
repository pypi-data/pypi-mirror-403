from fastapi import FastAPI, Depends, HTTPException
from mcp.server.fastmcp import FastMCP
from datetime import timedelta
from .schemas import UserProfile, Token
from .auth import (
    get_current_user, create_access_token, verify_password,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .tools import register_all_tools

from .database import query_db

app = FastAPI(title="University API")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: dict):
    # Depending on form_data structure, username might be 'username' or 'id'.
    # Assuming standard OAuth2 request where 'username' is the field name.
    username = form_data.get("username")
    password = form_data.get("password")

    # Query database for user
    user = query_db("SELECT * FROM users WHERE id = ?", (username,), one=True)

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=UserProfile)
async def read_users_me(current_user: str = Depends(get_current_user)):
    # get_current_user returns the username/id from the token
    user = query_db("SELECT * FROM users WHERE id = ?", (current_user.username,), one=True)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Map DB fields to UserProfile schema if needed (or if they match exactly)
    # UserProfile expects: id, name, email, role, department
    return user

mcp = FastMCP("university_mcp", instructions="Tools for university information access and management.")

register_all_tools(mcp)

# Mount SSE app
sse = mcp.sse_app()
app.mount("/mcp", sse)

if __name__ == "__main__":
    import sys
    # Check if we're running in stdio mode (for Claude Code CLI)
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Run HTTP server with SSE
        mcp.run()
    else:
        # Default to stdio transport for CLI usage
        mcp.run(transport="stdio")
