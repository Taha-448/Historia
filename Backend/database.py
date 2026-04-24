import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# --- CONTEXT HELPER ---
def set_pg_context(cursor, role: str):
    """Sets the role context in the current PG session for RLS enforcement."""
    cursor.execute(f"SET LOCAL app.current_user_role = %s", (role,))

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# --- USER MANAGEMENT ---
def get_user_by_username(username: str):
    """Retrieves a staff user profile by username."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM staff_users WHERE username = %s", (username,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_staff_user(username, hashed_password, role):
    """Creates a new staff member with a specific role."""
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO staff_users (username, hashed_password, role) VALUES (%s, %s, %s)",
            (username, hashed_password, role)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def initialize_db():
    """Creates necessary tables if they do not already exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    # Create the 'conversations' table as requested
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_input TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # The existing schema should be handled by schema.sql, 
    # but we ensure the basic structure if needed.
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized.")

def save_conversation(user_input, ai_response):
    """Inserts a user message and AI response pair into the conversations table."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_input, ai_response) VALUES (%s, %s)",
            (user_input, ai_response)
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error saving conversation: {e}")
    finally:
        conn.close()

def get_or_create_patient_session(phone_number: str) -> int:
    """Finds active session for a phone number, creates patient & session if missing."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor()
    
    try:
        # 1. Look up the Patient by phone number
        cursor.execute("SELECT patient_id FROM patients WHERE phone_number = %s", (phone_number,))
        patient = cursor.fetchone()
        
        if not patient:
            cursor.execute("INSERT INTO patients (phone_number) VALUES (%s) RETURNING patient_id", (phone_number,))
            patient_id = cursor.fetchone()[0]
        else:
            patient_id = patient[0]
            
        # 2. Look up the Patient's Active Session
        cursor.execute("SELECT session_id FROM chat_sessions WHERE patient_id = %s AND is_active = TRUE", (patient_id,))
        session = cursor.fetchone()
        
        if not session:
            cursor.execute("INSERT INTO chat_sessions (patient_id, is_active) VALUES (%s, TRUE) RETURNING session_id", (patient_id,))
            session_id = cursor.fetchone()[0]
        else:
            session_id = session[0]
            
        conn.commit()
        return session_id
    finally:
        cursor.close()
        conn.close()

def get_chat_history(session_id: int) -> str:
    """Retrieves all past messages for a specific session to feed to the AI."""
    conn = get_db_connection()
    if not conn: return ""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT sender_type, content FROM messages WHERE session_id = %s ORDER BY created_at", (session_id,))
        messages = cursor.fetchall()
        
        history_str = ""
        for msg in messages:
            if msg['sender_type'] == 'Human':
                history_str += f"Patient: {msg['content']}\n"
            else:
                history_str += f"Nurse: {msg['content']}\n"
        return history_str
    finally:
        cursor.close()
        conn.close()

def save_message(session_id: int, sender_type: str, content: str):
    """Logs a standalone message into the relational database."""
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO messages (session_id, sender_type, content) VALUES (%s, %s, %s)", (session_id, sender_type, content))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_active_sessions_list(role: str = 'nurse'):
    """Returns a list of all currently active triage patients, respects RLS."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        set_pg_context(cursor, role)
        cursor.execute("""
            SELECT 
                c.session_id, 
                p.phone_number, 
                c.created_at, 
                c.is_active,
                COALESCE(s.is_critical, FALSE) as is_critical
            FROM chat_sessions c
            JOIN patients p ON c.patient_id = p.patient_id
            LEFT JOIN triage_summaries s ON c.session_id = s.session_id
            WHERE c.is_active = TRUE OR s.is_critical = TRUE
            ORDER BY is_critical DESC, c.created_at DESC
        """)
        sessions = cursor.fetchall()
        for s in sessions:
            s['created_at'] = str(s['created_at'])
        return sessions
    finally:
        cursor.close()
        conn.close()

def verify_session_active(session_id: int):
    """Checks if a session exists and is active."""
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT session_id FROM chat_sessions WHERE session_id = %s AND is_active = TRUE", (session_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def insert_summary(session_id: int, summary_result: str, role: str = 'doctor'):
    """Inserts the generated summary into the database, respects RLS."""
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        set_pg_context(cursor, role)
        cursor.execute(
            "INSERT INTO triage_summaries (session_id, chief_complaint) VALUES (%s, %s)",
            (session_id, summary_result)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_weekly_analytics(role: str = 'doctor'):
    """Calls the stored procedure to get high-level weekly performance metrics, respects RLS."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        set_pg_context(cursor, role)
        cursor.execute("SELECT * FROM get_analytics_summary()")
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_symptom_data(role: str = 'doctor'):
    """Calls the stored procedure to get symptom frequency distribution, respects RLS."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        set_pg_context(cursor, role)
        cursor.execute("SELECT * FROM get_symptom_metrics()")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_audit_logs():
    """Retrieves the recent activity log from the database."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM audit_logs ORDER BY performed_at DESC LIMIT 20")
        logs = cursor.fetchall()
        for log in logs:
            log['performed_at'] = str(log['performed_at'])
        return logs
    finally:
        cursor.close()
        conn.close()
