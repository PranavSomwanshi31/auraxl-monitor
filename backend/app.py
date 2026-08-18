import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

from storage import (
    init_db, get_latest_scan, get_all_scans, get_scanned_pages,
    get_detected_issues, get_issue_by_id, get_notifications,
    mark_notification_read, mark_all_notifications_read, clear_all_notifications,
    get_all_settings, set_setting, get_setting
)
from auth import (
    ensure_default_admin, authenticate_user, validate_session,
    logout_session, update_user_password
)
from ai_agent import agent_engine
from monitor_service import monitor_service

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# Initialize Storage & Default Admin
init_db()
ensure_default_admin()

# Auth Middleware Helper
def get_authenticated_user():
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.args.get("token"):
        token = request.args.get("token")
    elif request.cookies.get("auraxl_token"):
        token = request.cookies.get("auraxl_token")
    return validate_session(token)

# --- Authentication Endpoints ---
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()
    
    if not user_id or not password:
        return jsonify({"success": False, "error": "UserID and Password are required."}), 400
        
    result = authenticate_user(user_id, password)
    if not result:
        return jsonify({"success": False, "error": "Invalid UserID or Password."}), 401
        
    return jsonify({"success": True, "data": result})

@app.route("/api/auth/verify", methods=["GET"])
def verify_auth():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "authenticated": False}), 401
    return jsonify({"success": True, "authenticated": True, "user": user})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        logout_session(token)
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/auth/update-password", methods=["POST"])
def update_password():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    old_pass = data.get("old_password", "")
    new_pass = data.get("new_password", "")
    
    ok, msg = update_user_password(user["user_id"], old_pass, new_pass)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

# --- Monitor & Health Endpoints ---
@app.route("/api/monitor/status", methods=["GET"])
def get_monitor_status():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    latest = get_latest_scan()
    is_scanning = monitor_service.is_currently_scanning()
    
    if not latest:
        summary = monitor_service.trigger_instant_scan()
        latest = get_latest_scan()
        
    return jsonify({
        "success": True,
        "is_scanning": is_scanning,
        "data": latest
    })

@app.route("/api/monitor/scan", methods=["POST"])
def trigger_scan():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    summary = monitor_service.trigger_instant_scan()
    return jsonify({"success": True, "data": summary})

@app.route("/api/monitor/pages", methods=["GET"])
def get_pages():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    scan_id = request.args.get("scan_id", type=int)
    pages = get_scanned_pages(scan_id)
    return jsonify({"success": True, "count": len(pages), "data": pages})

@app.route("/api/monitor/issues", methods=["GET"])
def get_issues():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    scan_id = request.args.get("scan_id", type=int)
    status = request.args.get("status")
    issues = get_detected_issues(scan_id=scan_id, status=status)
    return jsonify({"success": True, "count": len(issues), "data": issues})

@app.route("/api/monitor/issue/<int:issue_id>", methods=["GET"])
def get_issue(issue_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    issue = get_issue_by_id(issue_id)
    if not issue:
        return jsonify({"success": False, "error": "Issue not found"}), 404
    return jsonify({"success": True, "data": issue})

@app.route("/api/monitor/history", methods=["GET"])
def get_history():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    limit = request.args.get("limit", default=20, type=int)
    history = get_all_scans(limit=limit)
    return jsonify({"success": True, "count": len(history), "data": history})

# --- Notification Endpoints ---
@app.route("/api/notifications", methods=["GET"])
def notifications_feed():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    limit = request.args.get("limit", default=50, type=int)
    notifs = get_notifications(limit=limit)
    unread_count = sum(1 for n in notifs if n["is_read"] == 0)
    return jsonify({"success": True, "unread_count": unread_count, "data": notifs})

@app.route("/api/notifications/read/<int:notif_id>", methods=["POST"])
def mark_notif_read(notif_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    mark_notification_read(notif_id)
    return jsonify({"success": True})

@app.route("/api/notifications/read-all", methods=["POST"])
def mark_all_read():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    mark_all_notifications_read()
    return jsonify({"success": True})

@app.route("/api/notifications/clear", methods=["POST"])
def clear_notifs():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    clear_all_notifications()
    return jsonify({"success": True})

# --- Agentic AI Chat Assistant ---
@app.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "error": "Message is required."}), 400
        
    latest = get_latest_scan() or {}
    reply = agent_engine.chat_response(message, latest)
    return jsonify({"success": True, "reply": reply})

# --- App Settings ---
@app.route("/api/settings", methods=["GET"])
def get_settings():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    settings = get_all_settings()
    return jsonify({"success": True, "data": settings})

@app.route("/api/settings", methods=["POST"])
def update_settings():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    for k, v in data.items():
        set_setting(k, str(v))
        
    return jsonify({"success": True, "message": "Settings updated successfully."})

# --- Static Frontend & PWA Files ---
@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory(STATIC_DIR, "manifest.json", mimetype="application/manifest+json")

@app.route("/sw.js")
def serve_sw():
    return send_from_directory(STATIC_DIR, "sw.js", mimetype="application/javascript")

@app.route("/static/<path:path>")
def serve_static_explicit(path):
    return send_from_directory(STATIC_DIR, path)

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)

if __name__ == "__main__":
    monitor_service.start()
    port = int(os.environ.get("PORT", 5000))
    print(f"===========================================================")
    print(f"  [+] AuraXL Agentic AI Website Monitor & Diagnostic App")
    print(f"  [+] Mobile & Web URL: http://127.0.0.1:{port}")
    print(f"  [+] Default UserID:   admin")
    print(f"  [+] Default Password: AuraXL@2026")
    print(f"===========================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
