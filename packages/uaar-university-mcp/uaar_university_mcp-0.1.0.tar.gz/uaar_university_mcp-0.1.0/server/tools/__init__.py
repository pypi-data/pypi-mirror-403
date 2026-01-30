from .academic_tools import register_academic_tools
from .admission_tools import register_admission_tools
from .user_tools import register_user_tools
from .faculty_tools import register_faculty_tools
from .admission_form_tools import register_admission_form_tools
from .audit_tools import register_audit_tools
from .contact_tools import register_contact_tools
from .event_tools import register_event_tools
from .fee_tools import register_fee_tools
from .hostel_tools import register_hostel_tools
from .library_tools import register_library_tools
from .news_tools import register_news_tools
from .result_tools import register_result_tools
from .scholarship_tools import register_scholarship_tools
from .timetable_tools import register_timetable_tools
from .transport_tools import register_transport_tools
from .admin_tools import register_admin_tools

def register_all_tools(mcp):
    """Register all tool categories with the MCP server."""
    register_academic_tools(mcp)
    register_admission_tools(mcp)
    register_user_tools(mcp)
    register_faculty_tools(mcp)
    register_admission_form_tools(mcp)
    register_audit_tools(mcp)
    register_contact_tools(mcp)
    register_event_tools(mcp)
    register_fee_tools(mcp)
    register_hostel_tools(mcp)
    register_library_tools(mcp)
    register_news_tools(mcp)
    register_result_tools(mcp)
    register_scholarship_tools(mcp)
    register_timetable_tools(mcp)
    register_transport_tools(mcp)
    register_admin_tools(mcp)
