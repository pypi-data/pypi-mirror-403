from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, time

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str = Field(..., pattern="^(student|faculty|admin)$")
    department: Optional[str] = None

class Department(BaseModel):
    id: str
    name: str
    faculty: str
    description: Optional[str] = None

class Course(BaseModel):
    code: str
    title: str
    department_id: str
    credit_hours: int
    description: Optional[str] = None

class MeritListItem(BaseModel):
    rank: int
    student_name: str
    cnic_last_4: str
    aggregate_score: float
    status: str = "Selected"

class AdmissionStatus(BaseModel):
    cnic: str
    is_admitted: bool
    merit_rank: Optional[int] = None
    department: Optional[str] = None
    message: str

class NewsItem(BaseModel):
    id: str
    title: str
    date: str
    content: str
    category: str = Field(..., pattern="^(Academic|Admission|General|Event)$")

class FacultyMember(BaseModel):
    id: str
    name: str
    designation: str
    department: str
    email: str
    research_interests: List[str]

class Event(BaseModel):
    id: str
    title: str
    date: datetime
    location: str
    description: str

class FeeInfo(BaseModel):
    program: str
    admission_fee: float
    tuition_fee_per_semester: float
    total_first_semester: float

class AuditLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    tool_invoked: str
    status: str
    details: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ClassSchedule(BaseModel):
    course_code: str
    course_title: str
    day: str
    start_time: time
    end_time: time
    room: str
    instructor: str

class ExamSchedule(BaseModel):
    course_code: str
    course_title: str
    exam_date: datetime
    duration_hours: int
    venue: str
    exam_type: str

class LibraryBook(BaseModel):
    id: str
    title: str
    author: str
    isbn: str
    category: str
    available_copies: int
    total_copies: int
    location: str

class BookBorrowing(BaseModel):
    student_id: str
    book_id: str
    borrow_date: str
    due_date: str
    returned: bool = False
    return_date: Optional[str] = None

class HostelRoom(BaseModel):
    room_number: str
    hostel_name: str
    capacity: int
    occupied: int
    available: bool
    room_type: str
    monthly_rent: float

class MessMenu(BaseModel):
    day: str
    breakfast: str
    lunch: str
    dinner: str

class BusRoute(BaseModel):
    route_id: str
    route_name: str
    start_point: str
    end_point: str
    departure_time: time
    arrival_time: time
    fare: float
    stops: List[str]

class BusStop(BaseModel):
    stop_id: str
    name: str
    routes: List[str]
    pickup_time: time

class Scholarship(BaseModel):
    id: str
    name: str
    provider: str
    amount: float
    duration: str
    eligibility: List[str]
    deadline: str
    how_to_apply: str

class CourseResult(BaseModel):
    course_code: str
    course_title: str
    credit_hours: int
    grade: str
    grade_points: float

class SemesterResult(BaseModel):
    student_id: str
    semester: str
    courses: List[CourseResult]
    semester_gpa: float
    cumulative_gpa: float
    total_credits: int

class DepartmentContact(BaseModel):
    department: str
    phone: str
    email: str
    location: str
    hours: str

class HelpTicket(BaseModel):
    ticket_id: str
    student_id: str
    category: str
    subject: str
    description: str
    status: str = "Open"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdmissionForm(BaseModel):
    application_id: Optional[str] = None
    full_name: str
    father_name: str
    cnic: str
    date_of_birth: str
    gender: str
    email: str
    phone: str
    address: str
    city: str
    province: str
    domicile: str
    matric_board: str
    matric_year: int
    matric_marks_obtained: int
    matric_total_marks: int
    matric_percentage: float
    inter_board: str
    inter_year: int
    inter_marks_obtained: int
    inter_total_marks: int
    inter_percentage: float
    program_choice_1: str
    program_choice_2: Optional[str] = None
    program_choice_3: Optional[str] = None
    hostel_required: bool = False
    transport_required: bool = False
    status: str = "Draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdmissionFormDraft(BaseModel):
    application_id: str
    collected_fields: dict
    missing_fields: List[str]
    status: str = "Incomplete"

from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    count: int
    offset: int
    items: List[T]
    has_more: bool
    next_offset: Optional[int] = None
