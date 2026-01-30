from typing import List, Optional
from datetime import datetime
from server.schemas import ClassSchedule, ExamSchedule
from server.database import query_db

def register_timetable_tools(mcp):
    @mcp.tool(
        name="get_class_schedule",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_class_schedule(course_code: Optional[str] = None, day: Optional[str] = None) -> List[ClassSchedule]:
        """Get class schedule. Filter by course code or day of week."""
        sql = "SELECT * FROM class_schedule"
        params = []
        if course_code:
            sql += " WHERE course_code LIKE ?"
            params.append(f"%{course_code}%")
        if day:
            if params:
                sql += " AND day LIKE ?"
            else:
                sql += " WHERE day LIKE ?"
            params.append(f"%{day}%")

        rows = query_db(sql, tuple(params))
        return [ClassSchedule(**r) for r in rows]

    @mcp.tool(
        name="get_exam_schedule",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_exam_schedule(course_code: Optional[str] = None, exam_type: Optional[str] = None) -> List[ExamSchedule]:
        """Get exam schedule. Filter by course code or exam type (Midterm/Final)."""
        sql = "SELECT * FROM exam_schedule"
        params = []
        if course_code:
            sql += " WHERE course_code LIKE ?"
            params.append(f"%{course_code}%")
        if exam_type:
            if params:
                sql += " AND exam_type LIKE ?"
            else:
                sql += " WHERE exam_type LIKE ?"
            params.append(f"%{exam_type}%")

        rows = query_db(sql, tuple(params))
        return [ExamSchedule(**r) for r in rows]

    @mcp.tool(
        name="get_today_classes",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_today_classes() -> List[ClassSchedule]:
        """Get all classes scheduled for today."""
        today = datetime.now().strftime("%A")
        rows = query_db("SELECT * FROM class_schedule WHERE day LIKE ?", (f"%{today}%",))
        return [ClassSchedule(**r) for r in rows]
