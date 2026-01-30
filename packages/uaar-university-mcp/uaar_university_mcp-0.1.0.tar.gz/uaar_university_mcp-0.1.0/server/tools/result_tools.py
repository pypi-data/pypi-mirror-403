from typing import List, Optional
from server.schemas import CourseResult, SemesterResult
from server.database import query_db

def register_result_tools(mcp):
    @mcp.tool(
        name="get_semester_result",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_semester_result(student_id: str, semester: Optional[str] = None) -> List[SemesterResult]:
        """Get academic results for a student. Optionally filter by semester."""
        # This requires grouping query data by semester
        sql = "SELECT * FROM results WHERE student_id = ?"
        params = [student_id]
        if semester:
            sql += " AND semester LIKE ?"
            params.append(f"%{semester}%")

        rows = query_db(sql, tuple(params))

        # Group by semester
        semesters = {}
        for row in rows:
            sem = row['semester']
            if sem not in semesters:
                semesters[sem] = {
                    "student_id": student_id,
                    "semester": sem,
                    "courses": [],
                    "total_points": 0,
                    "total_credits": 0
                }
            # Add course info
            # We need course details (title, credit hours) which might be in 'courses' table
            # For efficiency we could JOIN, but simple lookup works for MVP or we just store it in results
            # The schema defined 'grade_points' but not full course details in 'results' table
            # Let's assume we can fetch course title/credits from courses table or they are passed in mocked data
            # To fix this properly, let's do a JOIN
            course_details = query_db("SELECT title, credit_hours FROM courses WHERE code = ?", (row['course_code'],), one=True)
            title = course_details['title'] if course_details else "Unknown Course"
            credits = course_details['credit_hours'] if course_details else 3 # Default fallback

            semesters[sem]["courses"].append(
                CourseResult(
                    course_code=row['course_code'],
                    course_title=title,
                    credit_hours=credits,
                    grade=row['grade'],
                    grade_points=row['grade_points']
                )
            )
            semesters[sem]["total_points"] += row['grade_points'] * credits
            semesters[sem]["total_credits"] += credits

        results = []
        cumulative_points = 0
        cumulative_credits = 0

        # Calculate GPAs
        # Note: CGPA logic is complex (accumulative over time), simplified here to just sum of what we found
        for sem, data in semesters.items():
            sem_gpa = data["total_points"] / data["total_credits"] if data["total_credits"] > 0 else 0
            cumulative_points += data["total_points"]
            cumulative_credits += data["total_credits"]
            cgpa = cumulative_points / cumulative_credits if cumulative_credits > 0 else 0

            results.append(SemesterResult(
                student_id=data["student_id"],
                semester=data["semester"],
                courses=data["courses"],
                semester_gpa=round(sem_gpa, 2),
                cumulative_gpa=round(cgpa, 2),
                total_credits=data["total_credits"]
            ))

        return results

    @mcp.tool(
        name="get_cgpa",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_cgpa(student_id: str) -> dict:
        """Get cumulative GPA and academic standing for a student."""
        # Calculate from all results
        rows = query_db("SELECT * FROM results WHERE student_id = ?", (student_id,))
        if not rows:
            return {"error": "Student not found or no results available"}

        total_points = 0
        total_credits = 0

        for row in rows:
            course = query_db("SELECT credit_hours FROM courses WHERE code = ?", (row['course_code'],), one=True)
            credits = course['credit_hours'] if course else 3
            total_points += row['grade_points'] * credits
            total_credits += credits

        cgpa = total_points / total_credits if total_credits > 0 else 0
        cgpa = round(cgpa, 2)

        standing = "Good Standing"
        if cgpa < 2.0:
            standing = "Academic Probation"
        elif cgpa >= 3.5:
            standing = "Dean's List"

        return {
            "student_id": student_id,
            "cumulative_gpa": cgpa,
            "total_credits": total_credits,
            "academic_standing": standing
        }

    @mcp.tool(
        name="calculate_gpa",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def calculate_gpa(grades: List[dict]) -> dict:
        """Calculate GPA from a list of grades. Input: [{'credit_hours': 3, 'grade': 'A'}, ...]"""
        # Fetch grade points from DB
        gp_rows = query_db("SELECT * FROM grade_points")
        grade_points = {row['grade']: row['points'] for row in gp_rows}

        # If DB is empty, faillback (should not happen if seeded)
        if not grade_points:
             grade_points = {"A": 4.0, "A-": 3.67, "B+": 3.33, "B": 3.0, "B-": 2.67, "C+": 2.33, "C": 2.0, "C-": 1.67, "D+": 1.33, "D": 1.0, "F": 0.0}

        total_points = 0
        total_credits = 0
        for g in grades:
            points = grade_points.get(g.get("grade", "F"), 0.0)
            credits = g.get("credit_hours", 0)
            total_points += points * credits
            total_credits += credits
        gpa = total_points / total_credits if total_credits > 0 else 0
        return {"gpa": round(gpa, 2), "total_credits": total_credits}

    @mcp.tool(
        name="get_transcript_request_info",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def get_transcript_request_info() -> dict:
        """Get information about requesting official transcripts."""
        return {
            "fee": 500,
            "processing_time": "3-5 working days",
            "how_to_apply": "Submit request at Examination Office with fee challan",
            "location": "Admin Block, Room 8",
            "hours": "9:00 AM - 2:00 PM (Mon-Fri)",
            "email": "examination@uaar.edu.pk",
            "documents_needed": ["Student ID card", "Fee challan"]
        }
