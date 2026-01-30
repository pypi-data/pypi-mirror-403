import sqlite3
import json
import bcrypt
from typing import List, Dict, Any, Optional
from datetime import datetime

import os

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "university.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        department TEXT,
        password_hash TEXT
    )''')

    # Departments
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faculty TEXT NOT NULL,
        description TEXT
    )''')

    # Courses
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        code TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        department_id TEXT NOT NULL,
        credit_hours INTEGER NOT NULL,
        description TEXT,
        FOREIGN KEY (department_id) REFERENCES departments (id)
    )''')

    # Faculty
    c.execute('''CREATE TABLE IF NOT EXISTS faculty (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        designation TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT NOT NULL,
        research_interests TEXT -- Storage: JSON string
    )''')

    # Events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT
    )''')

    # News
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL
    )''')

    # Library Books
    c.execute('''CREATE TABLE IF NOT EXISTS library_books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT,
        category TEXT,
        available_copies INTEGER,
        total_copies INTEGER,
        location TEXT
    )''')

    # Hostel Rooms
    c.execute('''CREATE TABLE IF NOT EXISTS hostel_rooms (
        room_number TEXT PRIMARY KEY,
        hostel_name TEXT NOT NULL,
        capacity INTEGER,
        occupied INTEGER,
        room_type TEXT,
        monthly_rent REAL,
        available BOOLEAN -- Store as 0 or 1
    )''')

    # Admission Forms
    c.execute('''CREATE TABLE IF NOT EXISTS admission_forms (
        application_id TEXT PRIMARY KEY,
        data TEXT NOT NULL, -- Storage: JSON string
        status TEXT NOT NULL,
        submitted_at TEXT
    )''')

    # Help Tickets
    c.execute('''CREATE TABLE IF NOT EXISTS help_tickets (
        ticket_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        category TEXT,
        subject TEXT,
        description TEXT,
        status TEXT,
        created_at TEXT
    )''')

    # Scholarships
    c.execute('''CREATE TABLE IF NOT EXISTS scholarships (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider TEXT,
        amount REAL,
        duration TEXT,
        eligibility TEXT, -- Storage: JSON string
        deadline TEXT,
        how_to_apply TEXT
    )''')

    # Bus Routes
    c.execute('''CREATE TABLE IF NOT EXISTS bus_routes (
        route_id TEXT PRIMARY KEY,
        route_name TEXT NOT NULL,
        start_point TEXT,
        end_point TEXT,
        departure_time TEXT,
        arrival_time TEXT,
        fare REAL,
        stops TEXT -- Storage: JSON string
    )''')

    # Fee Structure
    c.execute('''CREATE TABLE IF NOT EXISTS fees (
        program TEXT PRIMARY KEY,
        admission_fee REAL,
        tuition_fee_per_semester REAL,
        total_first_semester REAL
    )''')

    # Results
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        semester TEXT NOT NULL,
        course_code TEXT NOT NULL,
        grade TEXT,
        grade_points REAL
    )''')

    # Class Schedule
    c.execute('''CREATE TABLE IF NOT EXISTS class_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        day TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT,
        instructor TEXT
    )''')

    # Exam Schedule
    c.execute('''CREATE TABLE IF NOT EXISTS exam_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        exam_date TEXT NOT NULL,
        duration_hours INTEGER,
        venue TEXT,
        exam_type TEXT
    )''')

    # Mess Menu
    c.execute('''CREATE TABLE IF NOT EXISTS mess_menu (
        day TEXT PRIMARY KEY,
        breakfast TEXT,
        lunch TEXT,
        dinner TEXT
    )''')

    # Merit Lists
    c.execute('''CREATE TABLE IF NOT EXISTS merit_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id TEXT,
        rank INTEGER,
        student_name TEXT,
        cnic_last_4 TEXT,
        aggregate_score REAL,
        status TEXT
    )''')

    # Department Contacts
    c.execute('''CREATE TABLE IF NOT EXISTS department_contacts (
        department TEXT PRIMARY KEY,
        phone TEXT,
        email TEXT,
        location TEXT,
        hours TEXT
    )''')

    # Audit Logs
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        tool_invoked TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        details TEXT
    )''')

    # Emergency Contacts
    c.execute('''CREATE TABLE IF NOT EXISTS emergency_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        number TEXT NOT NULL
    )''')

    # University Info
    c.execute('''CREATE TABLE IF NOT EXISTS university_info (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )''')

    # Important Links
    c.execute('''CREATE TABLE IF NOT EXISTS important_links (
        key TEXT PRIMARY KEY,
        url TEXT NOT NULL
    )''')

    # Hostel Fees
    c.execute('''CREATE TABLE IF NOT EXISTS hostel_fees (
        room_type TEXT PRIMARY KEY,
        monthly_rent REAL,
        semester_fee REAL,
        security_deposit REAL
    )''')

    # Hostel Rules
    c.execute('''CREATE TABLE IF NOT EXISTS hostel_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule TEXT NOT NULL
    )''')

    # Transport Info
    c.execute('''CREATE TABLE IF NOT EXISTS transport_info (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )''')

    # Library Hours
    c.execute('''CREATE TABLE IF NOT EXISTS library_hours (
        day_type TEXT PRIMARY KEY,
        hours TEXT NOT NULL
    )''')

    # Admission Requirements
    c.execute('''CREATE TABLE IF NOT EXISTS admission_requirements (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL -- Store JSON array/object as string
    )''')

    # Available Programs (metadata for admission form)
    c.execute('''CREATE TABLE IF NOT EXISTS admission_programs (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        seats INTEGER NOT NULL
    )''')

    # Grade Points
    c.execute('''CREATE TABLE IF NOT EXISTS grade_points (
        grade TEXT PRIMARY KEY,
        points REAL NOT NULL
    )''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        # Generate hash for 'password123'
        pwd_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        c.execute("INSERT INTO users (id, name, email, role, department, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                  ('S123', 'Ali Khan', 'ali@university.edu', 'student', 'CS', pwd_hash))
        c.execute("INSERT INTO users (id, name, email, role, department, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                  ('admin', 'Admin User', 'admin@university.edu', 'admin', 'Admin', pwd_hash))

        # Seed Emergency Contacts
        c.executemany("INSERT OR IGNORE INTO emergency_contacts (key, number) VALUES (?, ?)", [
            ("security_emergency", "051-9290008"),
            ("health_emergency", "051-9290007"),
            ("fire_emergency", "1122"),
            ("ambulance", "115"),
            ("police", "15"),
            ("vice_chancellor_office", "051-9290100"),
            ("main_helpline", "051-9290000")
        ])

        # Seed University Info
        c.executemany("INSERT OR IGNORE INTO university_info (key, value) VALUES (?, ?)", [
            ("name", "PMAS Arid Agriculture University Rawalpindi (UAAR)"),
            ("established", "1970"),
            ("type", "Public"),
            ("chancellor", "Governor Punjab"),
            ("website", "https://www.uaar.edu.pk")
        ])

        # Seed Important Links
        c.executemany("INSERT OR IGNORE INTO important_links (key, url) VALUES (?, ?)", [
            ("main_portal", "https://www.uaar.edu.pk"),
            ("student_portal", "https://portal.uaar.edu.pk")
        ])

        # Seed Hostel Fees
        c.executemany("INSERT OR IGNORE INTO hostel_fees (room_type, monthly_rent, semester_fee, security_deposit) VALUES (?, ?, ?, ?)", [
            ("standard_room", 5000, 25000, 5000),
            ("single_room", 8000, 40000, 8000),
            ("mess_charges", 6000, 30000, 0) # Use mess_charges as a room_type for simplicity in this key-value model
        ])

        # Seed Hostel Rules
        c.executemany("INSERT OR IGNORE INTO hostel_rules (rule) VALUES (?)", [
            ("Gate closing time: 10:00 PM (weekdays), 11:00 PM (weekends)",),
            ("Visitors allowed only in common areas during visiting hours (4-6 PM)",)
        ])

        # Seed Transport Info
        c.executemany("INSERT OR IGNORE INTO transport_info (key, value) VALUES (?, ?)", [
            ("monthly_pass", "2000"),
            ("semester_pass", "10000"),
            ("annual_pass", "18000"),
            ("how_to_apply", "Visit Transport Office (Admin Block, Room 12) with fee receipt"),
            ("office_hours", "9:00 AM - 4:00 PM (Mon-Fri)"),
            ("contact", "transport@uaar.edu.pk")
        ])

        # Seed Library Hours
        c.executemany("INSERT OR IGNORE INTO library_hours (day_type, hours) VALUES (?, ?)", [
            ("monday_friday", "8:00 AM - 8:00 PM"),
            ("saturday", "9:00 AM - 5:00 PM"),
            ("sunday", "Closed"),
            ("ramadan_timing", "9:00 AM - 3:00 PM"),
            ("contact", "library@uaar.edu.pk") # storing contact here for simplicity
        ])

        # Seed Admission Requirements
        import json
        req_data = {
           "general_requirements": [
                "Pakistani National with valid CNIC",
                "Minimum 50% marks in Matriculation",
                "Minimum 50% marks in Intermediate/FSc/FA",
                "Age limit: Maximum 25 years for BS programs"
            ],
            "required_documents": [
                "Matriculation certificate (original + 2 copies)",
                "Intermediate certificate (original + 2 copies)",
                "CNIC (original + 2 copies)",
                "Domicile certificate",
                "6 passport size photographs",
                "Character certificate from last institution"
            ],
            "fee_structure": {
                "processing_fee": 2000,
                "admission_fee": 15000,
                "security_deposit": 5000,
                "tuition_fee_per_semester": "Varies by program (Rs. 35,000 - 50,000)"
            },
            "important_dates": {
                "form_submission_deadline": "2026-02-28",
                "entry_test_date": "2026-03-15",
                "merit_list_date": "2026-03-25",
                "fee_submission_deadline": "2026-04-05"
            }
        }
        for k, v in req_data.items():
            c.execute("INSERT OR IGNORE INTO admission_requirements (key, value) VALUES (?, ?)", (k, json.dumps(v)))

        # Seed Admission Programs
        programs = [
            {"code": "BSCS", "name": "BS Computer Science", "department": "UIIT", "seats": 120},
            {"code": "BSSE", "name": "BS Software Engineering", "department": "UIIT", "seats": 60},
            {"code": "BSIT", "name": "BS Information Technology", "department": "UIIT", "seats": 60},
            {"code": "BBA", "name": "Bachelor of Business Administration", "department": "UIMS", "seats": 100},
            {"code": "MBA", "name": "Master of Business Administration", "department": "UIMS", "seats": 50},
            {"code": "BSAg", "name": "BS Agriculture", "department": "Agriculture", "seats": 150},
            {"code": "DVM", "name": "Doctor of Veterinary Medicine", "department": "Veterinary", "seats": 80},
        ]
        c.executemany("INSERT OR IGNORE INTO admission_programs (code, name, department, seats) VALUES (?, ?, ?, ?)",
                      [(p['code'], p['name'], p['department'], p['seats']) for p in programs])


        # Seed Grade Points
        grade_points = [
            ("A", 4.0), ("A-", 3.67), ("B+", 3.33), ("B", 3.0),
            ("B-", 2.67), ("C+", 2.33), ("C", 2.0), ("C-", 1.67),
            ("D+", 1.33), ("D", 1.0), ("F", 0.0)
        ]
        c.executemany("INSERT OR IGNORE INTO grade_points (grade, points) VALUES (?, ?)", grade_points)

        conn.commit()
    conn.close()

# Initialize DB on import
init_db()
seed_db()

# --- Helper Functions ---

def query_db(query: str, args: tuple = (), one: bool = False):
    conn = get_db_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    if one:
        return dict(rv[0]) if rv else None
    return [dict(row) for row in rv]

def execute_db(query: str, args: tuple = ()):
    conn = get_db_connection()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
