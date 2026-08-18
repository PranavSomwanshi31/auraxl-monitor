import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from firebase_functions import https_fn
from firebase_admin import initialize_app
from flask import Flask, request, jsonify
from flask_cors import CORS

initialize_app()

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

flask_app = Flask(__name__)
CORS(flask_app)

try:
    init_db()
    ensure_default_admin()
    monitor_service.start()
except Exception as e:
    print(f"Startup init warning: {e}")

def get_authenticated_user():
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.args.get("token"):
        token = request.args.get("token")
    return validate_session(token)

@flask_app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    result = authenticate_user(data.get("user_id","").strip(), data.get("password","").strip())
    if not result:
        return jsonify({"success": False, "error": "Invalid UserID or Password."}), 401
    return jsonify({"success": True, "data": result})

@flask_app.route("/api/auth/verify", methods=["GET"])
def verify_auth():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "authenticated": False}), 401
    return jsonify({"success": True, "authenticated": True, "user": user})

@flask_app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        logout_session(auth_header[7:].strip())
    return jsonify({"success": True})

@flask_app.route("/api/auth/update-password", methods=["POST"])
def update_password():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.get_json() or {}
    ok, msg = update_user_password(user["user_id"], data.get("old_password",""), data.get("new_password",""))
    return jsonify({"success": ok, "message": msg} if ok else {"success": False, "error": msg}), 200 if ok else 400

@flask_app.route("/api/monitor/status", methods=["GET"])
def get_monitor_status():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    latest = get_latest_scan()
    if not latest:
        summary = monitor_service.trigger_instant_scan()
        latest = get_latest_scan()
    return jsonify({"success": True, "is_scanning": monitor_service.is_currently_scanning(), "data": latest})

@flask_app.route("/api/monitor/scan", methods=["POST"])
def trigger_scan():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    summary = monitor_service.trigger_instant_scan()
    return jsonify({"success": True, "data": summary})

@flask_app.route("/api/monitor/pages", methods=["GET"])
def get_pages():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    pages = get_scanned_pages(request.args.get("scan_id", type=int))
    return jsonify({"success": True, "count": len(pages), "data": pages})

@flask_app.route("/api/monitor/issues", methods=["GET"])
def get_issues():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    issues = get_detected_issues(scan_id=request.args.get("scan_id", type=int), status=request.args.get("status"))
    return jsonify({"success": True, "count": len(issues), "data": issues})

@flask_app.route("/api/monitor/issue/<int:issue_id>", methods=["GET"])
def get_issue(issue_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    issue = get_issue_by_id(issue_id)
    if not issue:
        return jsonify({"success": False, "error": "Issue not found"}), 404
    return jsonify({"success": True, "data": issue})

@flask_app.route("/api/monitor/history", methods=["GET"])
def get_history():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    history = get_all_scans(limit=request.args.get("limit", default=20, type=int))
    return jsonify({"success": True, "count": len(history), "data": history})

@flask_app.route("/api/notifications", methods=["GET"])
def notifications_feed():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    notifs = get_notifications(limit=request.args.get("limit", default=50, type=int))
    unread_count = sum(1 for n in notifs if n["is_read"] == 0)
    return jsonify({"success": True, "unread_count": unread_count, "data": notifs})

@flask_app.route("/api/notifications/read-all", methods=["POST"])
def mark_all_read():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    mark_all_notifications_read()
    return jsonify({"success": True})

@flask_app.route("/api/notifications/clear", methods=["POST"])
def clear_notifs():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    clear_all_notifications()
    return jsonify({"success": True})

@flask_app.route("/api/agent/chat", methods=["POST"])
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

@flask_app.route("/api/settings", methods=["GET"])
def get_settings():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return jsonify({"success": True, "data": get_all_settings()})

@flask_app.route("/api/settings", methods=["POST"])
def update_settings():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.get_json() or {}
    for k, v in data.items():
        set_setting(k, str(v))
    return jsonify({"success": True, "message": "Settings updated."})

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    with flask_app.request_context(req.environ):
        try:
            rv = flask_app.preprocess_request()
            if rv is None:
                rv = flask_app.dispatch_request()
        except Exception as e:
            rv = flask_app.handle_user_exception(e)
        response = flask_app.make_response(rv)
        return flask_app.process_response(response)
