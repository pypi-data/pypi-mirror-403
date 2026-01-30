# UAAR University MCP Server

A Model Context Protocol (MCP) server for UAAR University, providing AI agents with access to academic resources, admissions, student services, and more.

## Features

- **Academic Resources**: Course search, department information.
- **Faculty Directory**: Search faculty by name or research interest.
- **Admissions**: Check merit lists, admission status, and online application.
- **Student Services**: Library, Hostel, Transport, and Scholarship information.
- **Results & Exams**: Check semester results, CGPA, and exam schedules.
- **Campus Life**: Events, News, and Cafeteria menus.
- **Support**: Help desk ticketing and emergency contacts.

## Tools Available

### Academic
- `list_departments`: List all academic departments.
- `search_courses`: Search for courses by name or code.

### Admission
- `get_merit_list`: Get merit lists for Spring 2026.
- `check_admission_status`: Check status by CNIC.
- `start_admission_form`: Start a new admission application.
- `get_admission_requirements`: Get eligibility criteria and guidelines.

### Student Services
- `search_library_books`: Search library catalog.
- `check_hostel_availability`: Check room availability.
- `get_bus_routes`: View transport routes.
- `list_scholarships`: Browse available scholarships.

### Results & Exams
- `get_semester_result`: View student results.
- `get_class_schedule`: Get weekly timetable.

## Setup & Running

### Prerequisites
- Python 3.10+
- `uv` (recommended) or `pip`

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd server
   ```

2. Install dependencies:
   ```bash
   uv sync
   # OR
   pip install -r requirements.txt
   ```

### Running the Server

Run the server using `uv`:

```bash
uv run server/main.py
```

Or using python directly:

```bash
python server/main.py
```

## Integration with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uaar-university": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/server",
        "run",
        "server/main.py"
      ]
    }
  }
}
```

## Evaluation

To run the evaluation suite:

```bash
python scripts/evaluation.py -t stdio -c python -a server/main.py server/evaluation.xml
```

## License

MIT License
