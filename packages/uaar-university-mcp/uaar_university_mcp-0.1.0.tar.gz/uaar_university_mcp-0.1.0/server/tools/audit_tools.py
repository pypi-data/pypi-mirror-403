from server.schemas import AuditLog
from server.database import execute_db

def register_audit_tools(mcp):
    @mcp.tool(
        name="log_interaction",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def log_interaction(agent_id: str, tool: str, details: str) -> str:
        """Log an AI agent interaction for auditing purposes."""

        # Insert into database
        log_id = execute_db(
            "INSERT INTO audit_logs (agent_id, tool_invoked, status, details) VALUES (?, ?, ?, ?)",
            (agent_id, tool, "Success", details)
        )

        return f"Logged successfully with ID: {log_id}"
