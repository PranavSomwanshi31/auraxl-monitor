import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from storage import get_connection

DEFAULT_USER = "admin"
DEFAULT_PASS = "AuraXL@2026"
SESSION_DURATION_DAYS = 30

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, password_hash)

def ensure_default_admin():
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (DEFAULT_USER,)).fetchone()
    if not user:
        p_hash, salt = hash_password(DEFAULT_PASS)
        now = datetime.now().isoformat()
        conn.execute("""
        INSERT INTO users (user_id, password_hash, salt, created_at, role, display_name)
        VALUES (?, ?, ?, ?, 'admin', 'AuraXL Administrator')
        """, (DEFAULT_USER, p_hash, salt, now))
        conn.commit()
    conn.close()

def authenticate_user(user_id: str, password: str) -> Optional[Dict]:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None
    
    if not verify_password(password, user["password_hash"], user["salt"]):
        conn.close()
        return None

    # Update last login
    now = datetime.now().isoformat()
    conn.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (now, user_id))
    
    # Create session token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=SESSION_DURATION_DAYS)).isoformat()
    conn.execute("""
    INSERT INTO sessions (token, user_id, created_at, expires_at)
    VALUES (?, ?, ?, ?)
    """, (token, user_id, now, expires_at))
    conn.commit()
    conn.close()

    return {
        "user_id": user["user_id"],
        "display_name": user["display_name"],
        "role": user["role"],
        "token": token,
        "expires_at": expires_at
    }

def validate_session(token: str) -> Optional[Dict]:
    if not token:
        return None
    conn = get_connection()
    row = conn.execute("""
    SELECT s.token, s.user_id, s.expires_at, u.role, u.display_name
    FROM sessions s
    JOIN users u ON s.user_id = u.user_id
    WHERE s.token = ?
    """, (token,)).fetchone()
    conn.close()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now() > expires_at:
        # Expired
        return None

    return {
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "role": row["role"]
    }

def update_user_password(user_id: str, old_pass: str, new_pass: str) -> tuple[bool, str]:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return False, "User not found."

    if not verify_password(old_pass, user["password_hash"], user["salt"]):
        conn.close()
        return False, "Current password is incorrect."

    if len(new_pass) < 6:
        conn.close()
        return False, "New password must be at least 6 characters."

    p_hash, salt = hash_password(new_pass)
    conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?", (p_hash, salt, user_id))
    conn.commit()
    conn.close()
    return True, "Password updated successfully."

def logout_session(token: str):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
