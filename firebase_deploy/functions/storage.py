import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "monitor.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT,
        role TEXT DEFAULT 'admin',
        display_name TEXT DEFAULT 'Site Admin'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_url TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        health_score INTEGER DEFAULT 100,
        total_pages_scanned INTEGER DEFAULT 0,
        broken_links_count INTEGER DEFAULT 0,
        issues_count INTEGER DEFAULT 0,
        ssl_status TEXT,
        dns_status TEXT,
        response_time_ms REAL DEFAULT 0,
        summary_json TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scanned_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER,
        url TEXT NOT NULL,
        path TEXT NOT NULL,
        status_code INTEGER,
        response_time_ms REAL,
        title TEXT,
        issues_json TEXT,
        links_found INTEGER DEFAULT 0,
        assets_found INTEGER DEFAULT 0,
        last_scanned TEXT,
        FOREIGN KEY (scan_id) REFERENCES scan_history (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detected_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER,
        page_url TEXT NOT NULL,
        error_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        root_cause TEXT NOT NULL,
        user_fix_steps TEXT NOT NULL,
        support_ticket_template TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN',
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        FOREIGN KEY (scan_id) REFERENCES scan_history (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        related_url TEXT,
        category TEXT DEFAULT 'HEALTH'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Default settings
    default_settings = {
        "target_url": "https://www.amazon.in",
        "monitor_interval_minutes": "5",
        "auto_monitor_enabled": "true",
        "sound_alerts": "true",
        "push_alerts": "true",
        "max_crawl_depth": "3",
        "max_crawl_pages": "50",
        "webhook_url": ""
    }

    for key, val in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()

# Settings Helpers
def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def get_all_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# Notification Helpers
def add_notification(title: str, message: str, severity: str = "INFO", related_url: str = "", category: str = "HEALTH") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO notifications (title, message, severity, timestamp, is_read, related_url, category)
    VALUES (?, ?, ?, ?, 0, ?, ?)
    """, (title, message, severity, now, related_url, category))
    notif_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return notif_id

def get_notifications(limit: int = 50) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_notification_read(notif_id: int):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()

def mark_all_notifications_read():
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read = 1")
    conn.commit()
    conn.close()

def clear_all_notifications():
    conn = get_connection()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    conn.close()

# Scan & Issue Helpers
def save_scan_summary(target_url: str, status: str, health_score: int, total_pages: int, 
                      broken_links: int, issues_count: int, ssl_status: str, dns_status: str, 
                      response_time_ms: float, summary_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO scan_history (target_url, timestamp, status, health_score, total_pages_scanned, 
                              broken_links_count, issues_count, ssl_status, dns_status, response_time_ms, summary_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (target_url, now, status, health_score, total_pages, broken_links, issues_count, 
          ssl_status, dns_status, response_time_ms, json.dumps(summary_data)))
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id

def save_scanned_page(scan_id: int, url: str, path: str, status_code: Optional[int], 
                      response_time_ms: float, title: str, issues: list, links_found: int, assets_found: int):
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute("""
    INSERT INTO scanned_pages (scan_id, url, path, status_code, response_time_ms, title, issues_json, links_found, assets_found, last_scanned)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scan_id, url, path, status_code, response_time_ms, title, json.dumps(issues), links_found, assets_found, now))
    conn.commit()
    conn.close()

def save_detected_issue(scan_id: int, page_url: str, error_type: str, severity: str, 
                        title: str, description: str, root_cause: str, user_fix_steps: Any, 
                        support_ticket_template: str):
    conn = get_connection()
    now = datetime.now().isoformat()
    
    steps_str = json.dumps(user_fix_steps) if isinstance(user_fix_steps, (list, dict)) else str(user_fix_steps)

    conn.execute("""
    INSERT INTO detected_issues (scan_id, page_url, error_type, severity, title, description, root_cause, user_fix_steps, support_ticket_template, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (scan_id, page_url, error_type, severity, title, description, root_cause, steps_str, support_ticket_template, now))
    conn.commit()
    conn.close()

def get_latest_scan() -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM scan_history ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        res = dict(row)
        if res.get("summary_json"):
            try:
                res["summary"] = json.loads(res["summary_json"])
            except Exception:
                res["summary"] = {}
        return res
    return None

def get_all_scans(limit: int = 20) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM scan_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_scanned_pages(scan_id: Optional[int] = None) -> List[Dict]:
    conn = get_connection()
    if scan_id:
        rows = conn.execute("SELECT * FROM scanned_pages WHERE scan_id = ? ORDER BY id ASC", (scan_id,)).fetchall()
    else:
        rows = conn.execute("""
        SELECT * FROM scanned_pages 
        WHERE scan_id = (SELECT id FROM scan_history ORDER BY id DESC LIMIT 1) 
        ORDER BY id ASC
        """).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("issues_json"):
            try:
                d["issues"] = json.loads(d["issues_json"])
            except Exception:
                d["issues"] = []
        else:
            d["issues"] = []
        result.append(d)
    return result

def get_detected_issues(scan_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
    conn = get_connection()
    query = "SELECT * FROM detected_issues"
    params = []
    conditions = []
    
    if scan_id:
        conditions.append("scan_id = ?")
        params.append(scan_id)
    else:
        conditions.append("scan_id = (SELECT id FROM scan_history ORDER BY id DESC LIMIT 1)")
        
    if status:
        conditions.append("status = ?")
        params.append(status)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, id DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    result = []
    for r in rows:
        d = dict(r)
        if d.get("user_fix_steps"):
            try:
                d["user_fix_steps"] = json.loads(d["user_fix_steps"])
            except Exception:
                pass
        result.append(d)
    return result

def get_issue_by_id(issue_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM detected_issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("user_fix_steps"):
            try:
                d["user_fix_steps"] = json.loads(d["user_fix_steps"])
            except Exception:
                pass
        return d
    return None
