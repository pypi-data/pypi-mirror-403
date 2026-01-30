# UAAR University MCP Server

[![PyPI version](https://img.shields.io/pypi/v/uaar-university-mcp.svg)](https://pypi.org/project/uaar-university-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/uaar-university-mcp.svg)](https://pypi.org/project/uaar-university-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for UAAR University, providing AI agents with access to academic resources, admissions, student services, and more.

## Features

- **Academic Resources**: Course search, department information, merit lists
- **Faculty Directory**: Search faculty by name or research interest
- **Student Services**: Library, Hostel, Transport, and Scholarship information
- **Results & Exams**: Check semester results, CGPA, and exam schedules
- **Admissions**: Check admission status, admission forms, and programs
- **Administrative Tools**: Contact information, event listings, fee structures
- **Admin Features**: Add departments, courses, faculty, events, scholarships

## Installation

### From PyPI

```bash
pip install uaar-university-mcp
```

### Using uv

```bash
uv add uaar-university-mcp
```

## Usage

### As a Standalone MCP Server

```bash
# Run with stdio transport (for Claude Code CLI)
python -m server.cli

# Or run the HTTP server with SSE
python -m server.main --http
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "uaar-university": {
      "command": "python",
      "args": [
        "-m",
        "server.cli"
      ]
    }
  }
}
```

### Integration with Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "uaar-university": {
      "command": "uv",
      "args": [
        "run",
        "-m",
        "server.cli"
      ]
    }
  }
}
```

## Available Tools

The MCP server provides over 50 tools across these categories:

### Academic Tools
- Search courses by name or code
- List academic departments
- Get merit lists by department
- Get class and exam schedules

### Student Services
- Check admission status
- Get semester results and CGPA
- Search library books
- Check hostel availability
- Get scholarship information

### Faculty & Administration
- Search faculty members
- Get department contact information
- List upcoming events
- Get news and announcements

### Administrative Tools (Admin only)
- Add new departments, courses, faculty
- Add library books and scholarships
- Add university events and news

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/uaar-university/uaar-university-mcp.git
cd uaar-university-mcp

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Running in Development

```bash
# Run with stdio transport (for testing with Claude Code)
uv run python -m server.cli

# Or run HTTP server for testing SSE
uv run python -m server.main --http
```

## Configuration

The server uses a SQLite database by default. To use a different database:

1. Copy `.env.example` to `.env`
2. Update the database connection string

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/)
- Uses [FastMCP](https://github.com/modelcontextprotocol/python-sdk) from the MCP Python SDK
- Inspired by educational technology initiatives at UAAR University
