import sqlite3
import time

DB_FILE = "land_analytics.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            action TEXT,
            target_id TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            project_type TEXT,
            district TEXT,
            state TEXT,
            land_area_hectares REAL,
            affected_families_count INTEGER,
            compensation_disbursed_pct REAL,
            pending_approvals_days INTEGER,
            legal_disputes_count INTEGER,
            possession_status_pct REAL,
            rehabilitation_progress_pct REAL,
            stakeholder_responsiveness_score REAL,
            historical_admin_performance REAL,
            documentation_incomplete_pct REAL,
            risk_score REAL,
            risk_category TEXT,
            sec4_prob REAL,
            sec11_prob REAL,
            sec23_prob REAL,
            primary_driver TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_security_action(username, action, target_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audit_logs (timestamp, username, action, target_id) VALUES (?, ?, ?, ?)", 
                   (time.strftime('%Y-%m-%d %H:%M:%S'), username, action, str(target_id)))
    conn.commit()
    conn.close()

def create_user_profile(username, password, role):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user_session(username, password):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def save_analytical_project(p: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO land_projects (
            project_name, project_type, district, state, land_area_hectares, affected_families_count,
            compensation_disbursed_pct, pending_approvals_days, legal_disputes_count, possession_status_pct,
            rehabilitation_progress_pct, stakeholder_responsiveness_score, historical_admin_performance,
            documentation_incomplete_pct, risk_score, risk_category, sec4_prob, sec11_prob, sec23_prob, primary_driver
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p['project_name'], p['project_type'], p['district'], p['state'], p['land_area_hectares'], p['affected_families_count'],
        p['compensation_disbursed_pct'], p['pending_approvals_days'], p['legal_disputes_count'], p['possession_status_pct'],
        p['rehabilitation_progress_pct'], p['stakeholder_responsiveness_score'], p['historical_admin_performance'],
        p['documentation_incomplete_pct'], p['risk_score'], p['risk_category'], p['sec4_prob'], p['sec11_prob'], p['sec23_prob'], p['primary_driver']
    ))
    conn.commit()
    conn.close()

def fetch_project_by_id(project_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM land_projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return project

def update_analytical_project(project_id: int, p: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE land_projects SET
            project_name = ?, project_type = ?, district = ?, state = ?,
            land_area_hectares = ?, affected_families_count = ?, compensation_disbursed_pct = ?,
            pending_approvals_days = ?, legal_disputes_count = ?, possession_status_pct = ?,
            rehabilitation_progress_pct = ?, stakeholder_responsiveness_score = ?,
            historical_admin_performance = ?, documentation_incomplete_pct = ?,
            risk_score = ?, risk_category = ?, sec4_prob = ?, sec11_prob = ?, sec23_prob = ?, primary_driver = ?
        WHERE id = ?
    ''', (
        p['project_name'], p['project_type'], p['district'], p['state'], p['land_area_hectares'], p['affected_families_count'],
        p['compensation_disbursed_pct'], p['pending_approvals_days'], p['legal_disputes_count'], p['possession_status_pct'],
        p['rehabilitation_progress_pct'], p['stakeholder_responsiveness_score'], p['historical_admin_performance'],
        p['documentation_incomplete_pct'], p['risk_score'], p['risk_category'], p['sec4_prob'], p['sec11_prob'], p['sec23_prob'],
        p['primary_driver'], project_id
    ))
    conn.commit()
    conn.close()

def delete_analytical_project(project_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM land_projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def fetch_all_project_records(limit=10):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM land_projects ORDER BY created_at DESC LIMIT ?', (limit,))
    records = cursor.fetchall()
    conn.close()
    return records

def search_project_records(query: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    search_term = f"%{query}%"
    cursor.execute('''
        SELECT * FROM land_projects 
        WHERE project_name LIKE ? OR district LIKE ? OR state LIKE ? OR project_type LIKE ?
        ORDER BY created_at DESC
    ''', (search_term, search_term, search_term, search_term))
    records = cursor.fetchall()
    conn.close()
    return records

def fetch_total_count():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM land_projects')
    count = cursor.fetchone()[0]
    conn.close()
    return count