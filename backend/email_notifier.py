import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from storage import get_setting, add_notification

def send_email_alert(title: str, severity: str, details: str, issue_data: dict = None, recipient: str = None) -> bool:
    """
    Sends an automated email alert when an outage, SSL drop, or critical event occurs.
    """
    enabled = get_setting("email_alerts_enabled", "true").lower() == "true"
    if not enabled:
        return False

    to_email = recipient or get_setting("alert_email", "31pranav104@gmail.com")
    if not to_email:
        return False

    smtp_server = get_setting("smtp_server", "smtp.gmail.com")
    smtp_port = int(get_setting("smtp_port", "587"))
    smtp_user = get_setting("smtp_user", "")
    smtp_pass = get_setting("smtp_password", "")

    # If no custom SMTP credentials provided, log notification & note
    if not smtp_user or not smtp_pass:
        add_notification(
            title=f"Email Alert Queued: {title}",
            message=f"Alert generated for {to_email}. Configure SMTP password in Settings to enable direct delivery.",
            severity="INFO",
            category="EMAIL"
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{severity.upper()}] AuraXL Website Alert: {title}"
        msg["From"] = f"AuraXL AI Monitor <{smtp_user}>"
        msg["To"] = to_email

        target_url = get_setting("target_url", "https://www.auraxl.com")
        color = "#F26727" if severity.upper() == "CRITICAL" else "#0DB2A7"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; color: #334155;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #2BC0D4, #0DB2A7); padding: 24px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800;">AuraXL AI Monitor Alert</h1>
                    <p style="color: #e6f7f6; margin: 6px 0 0 0; font-size: 13px;">Target Website: {target_url}</p>
                </div>
                <div style="padding: 24px;">
                    <div style="display: inline-block; padding: 6px 14px; border-radius: 20px; background-color: {color}20; color: {color}; font-weight: bold; font-size: 12px; margin-bottom: 16px; text-transform: uppercase;">
                        Severity: {severity}
                    </div>
                    <h2 style="color: #1e293b; margin: 0 0 12px 0; font-size: 18px;">{title}</h2>
                    <div style="background: #f1f5f9; border-left: 4px solid {color}; padding: 14px; border-radius: 8px; font-size: 14px; line-height: 1.6; margin-bottom: 20px;">
                        {details}
                    </div>
                    <p style="font-size: 12px; color: #64748b; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 16px;">
                        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                        Sent automatically by AuraXL Agentic AI 24/7 Monitor.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        if smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_email, msg.as_string())

        add_notification(
            title=f"Email Dispatched: {title}",
            message=f"Alert successfully sent to {to_email}.",
            severity="SUCCESS",
            category="EMAIL"
        )
        return True
    except Exception as e:
        print(f"[Email Alert Error] {e}")
        add_notification(
            title="Email Dispatch Failed",
            message=f"Could not send email to {to_email}: {str(e)}",
            severity="WARNING",
            category="EMAIL"
        )
        return False
