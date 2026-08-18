import json
import re
from typing import Dict, List, Any, Optional

class AgenticAIEngine:
    """
    Intelligent Agentic Diagnostic & User Remedy Engine for Website Health.
    Formulates clear, non-code, step-by-step user-actionable solutions (dashboard settings,
    DNS adjustments, SSL toggles, hosting panel steps, and ready-to-send support tickets).
    """

    def diagnose_issue(self, error_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw crawler diagnostic context and produces a comprehensive non-code solution.
        """
        url = context.get("url", "https://www.auraxl.com")
        ip = context.get("ip", "34.120.137.41")
        details = context.get("details", "")

        if error_type == "SSL_HANDSHAKE_EOF" or "UNEXPECTED_EOF_WHILE_READING" in details or "Server disconnected without sending a response" in details:
            return self._diagnose_ssl_eof(url, ip, details)
        elif error_type == "HTTP_502_BAD_GATEWAY" or "502" in details:
            return self._diagnose_502(url, ip, details)
        elif error_type == "HTTP_500_SERVER_ERROR" or "500" in details:
            return self._diagnose_500(url, ip, details)
        elif error_type == "HTTP_404_NOT_FOUND" or "404" in details:
            return self._diagnose_404(url, context.get("path", "/"), details)
        elif error_type == "HTTP_403_FORBIDDEN" or "403" in details:
            return self._diagnose_403(url, details)
        elif error_type == "DNS_RESOLUTION_FAILURE":
            return self._diagnose_dns(url, details)
        elif error_type == "SLOW_PAGE_RESPONSE":
            return self._diagnose_slow_page(url, context.get("response_time_ms", 0))
        elif error_type == "MIXED_CONTENT":
            return self._diagnose_mixed_content(url, details)
        elif error_type == "MISSING_SECURITY_HEADERS":
            return self._diagnose_security_headers(url, details)
        elif error_type == "BROKEN_LINK_OR_ASSET":
            return self._diagnose_broken_asset(url, details)
        else:
            return self._diagnose_generic(url, error_type, details)

    def _diagnose_ssl_eof(self, url: str, ip: str, details: str) -> Dict[str, Any]:
        return {
            "title": "Server Disconnecting / SSL Handshake Interruption",
            "severity": "CRITICAL",
            "error_type": "SSL_HANDSHAKE_EOF",
            "plain_explanation": f"The web server at {ip} accepted the network connection but abruptly hung up before completing the secure SSL/HTTPS handshake. Visitors attempting to open {url} cannot see the website and receive a connection drop or SSL protocol error.",
            "root_cause": "The reverse proxy / Cloud Load Balancer (IP 34.120.137.41) does not have an active SSL certificate attached, or the backend origin web server service is not running / failing health checks.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Check Cloudflare / CDN SSL/TLS Encryption Mode",
                    "action": "If your domain uses Cloudflare or another CDN, log into the dashboard, navigate to 'SSL/TLS' > 'Overview', and ensure the mode is set to 'Full' or 'Full (strict)' if your origin has a certificate, or 'Flexible' if your origin server runs on port 80 (HTTP)."
                },
                {
                    "step": 2,
                    "title": "Verify Domain DNS & Server IP Assignment",
                    "action": f"Log into your Domain Registrar (Namecheap, GoDaddy, Google Domains, etc.) or Cloudflare DNS manager. Check if the 'A' record for '{url}' is pointing to the correct active hosting IP ({ip}). If you migrated hosting recently, update the A record to your new hosting server IP."
                },
                {
                    "step": 3,
                    "title": "Re-Issue / Re-enable SSL Certificate in Hosting Panel",
                    "action": "Log into your Hosting Control Panel (cPanel, Plesk, Hostinger, GCP, or AWS Console). Go to 'SSL/TLS' or 'Security Certificates'. Click 'AutoSSL / Reinstall Let's Encrypt Certificate' and ensure the certificate covers both 'auraxl.com' and 'www.auraxl.com'."
                },
                {
                    "step": 4,
                    "title": "Restart Web Server Service / Check Origin Health",
                    "action": "In your hosting panel or Cloud Console, verify that the web service (Nginx/Apache/Node/Gunicorn) is started and healthy. If on Google Cloud (GCP) or AWS, check the Load Balancer Backend Health status to ensure the backend instance is marked 'HEALTHY'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Urgent: Server dropping connections / SSL handshake EOF on www.auraxl.com (IP: {ip})

Dear Hosting Support Team,

I am experiencing an urgent downtime issue on my website www.auraxl.com pointing to server IP {ip}.

Problem Description:
The server is terminating TCP connections immediately during the SSL/HTTPS handshake with the error '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol' and 'Server disconnected without sending a response'.

Diagnostics:
- Target Host: www.auraxl.com / auraxl.com
- Resolved IP: {ip}
- Issue: Web service or Load Balancer backend is not returning response headers / SSL handshake failure.

Could you please check:
1. Is the web server service running and listening on port 80 and 443?
2. Is the SSL/TLS certificate properly installed and bound to the domain?
3. If this is behind a Cloud Load Balancer/Reverse Proxy, are the origin backend health checks passing?

Thank you for your prompt assistance."""
        }

    def _diagnose_502(self, url: str, ip: str, details: str) -> Dict[str, Any]:
        return {
            "title": "502 Bad Gateway - Backend Server Offline",
            "severity": "CRITICAL",
            "error_type": "HTTP_502_BAD_GATEWAY",
            "plain_explanation": f"The front-end web server received an invalid or empty response from the backend application running {url}.",
            "root_cause": "The backend application service (Node.js, PHP-FPM, Python, Docker, or Database) has crashed, stopped running, or ran out of server memory.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Restart Application Service in Hosting Control Panel",
                    "action": "Log into your hosting dashboard (cPanel / Cloudways / AWS / Hostinger). Navigate to 'Application Manager' or 'Process Management' and click 'Restart App' or 'Restart PHP-FPM / Node.js'."
                },
                {
                    "step": 2,
                    "title": "Check Server Resource Usage (RAM & CPU)",
                    "action": "Check the Server Health monitor in your hosting panel. If RAM is at 100%, reboot the server instance or increase memory allocation."
                },
                {
                    "step": 3,
                    "title": "Verify Database Connection",
                    "action": "Ensure your MySQL / PostgreSQL database server is active and accessible."
                }
            ],
            "support_ticket_template": f"""SUBJECT: 502 Bad Gateway error on www.auraxl.com

Dear Technical Support,

My website www.auraxl.com is returning a 502 Bad Gateway error. It appears the upstream backend application service or PHP/Node handler is unresponsive.

Could you please inspect the server logs, restart the application backend service, and verify server memory status?

Thank you."""
        }

    def _diagnose_500(self, url: str, ip: str, details: str) -> Dict[str, Any]:
        return {
            "title": "500 Internal Server Error",
            "severity": "CRITICAL",
            "error_type": "HTTP_500_SERVER_ERROR",
            "plain_explanation": f"The website server encountered an unexpected error while executing the page request for {url}.",
            "root_cause": "An application runtime error, misconfigured .htaccess file, bad plugin/theme, or missing environment configuration.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Check Error Logs in Hosting Control Panel",
                    "action": "Log into cPanel / Hosting Dashboard > 'Metrics' > 'Errors' or 'File Manager' > 'logs/error_log' to view the specific crash reason."
                },
                {
                    "step": 2,
                    "title": "Reset or Verify .htaccess Configuration",
                    "action": "In File Manager, temporarily rename '.htaccess' to '.htaccess_backup' to verify if a rewrite rule syntax error is causing the crash."
                },
                {
                    "step": 3,
                    "title": "Disable Recently Added Plugins / Modules",
                    "action": "If using WordPress or a CMS, disable recently updated plugins or switch to the default theme."
                }
            ],
            "support_ticket_template": f"""SUBJECT: 500 Internal Server Error on www.auraxl.com

Dear Support,

Our website www.auraxl.com is throwing a 500 Internal Server Error. Please inspect the web server error log to identify the fatal error or permission issue.

Thank you."""
        }

    def _diagnose_404(self, url: str, path: str, details: str) -> Dict[str, Any]:
        return {
            "title": f"404 Page Not Found: {path}",
            "severity": "MEDIUM",
            "error_type": "HTTP_404_NOT_FOUND",
            "plain_explanation": f"Visitors clicking on the link '{path}' are encountering a dead page. The requested resource does not exist on the server.",
            "root_cause": "The page URL was moved, deleted, renamed, or a menu navigation link has a typo.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Set Up a 301 Redirect in Hosting / CMS Dashboard",
                    "action": f"In your Hosting cPanel > 'Redirects' (or WordPress Redirection plugin / Cloudflare Page Rules), set up a 301 permanent redirect from '{path}' to the active destination page or homepage."
                },
                {
                    "step": 2,
                    "title": "Update Broken Links in Navigation Menu",
                    "action": f"Check your website's header/footer menu settings in your CMS or site builder and correct the hyperlink for '{path}'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Inquiry regarding 404 URL rewrite on www.auraxl.com

Dear Support,

Please confirm if URL rewriting (mod_rewrite / Nginx try_files) is active on our hosting account so that routing for '{path}' works properly.

Thank you."""
        }

    def _diagnose_403(self, url: str, details: str) -> Dict[str, Any]:
        return {
            "title": "403 Forbidden - Access Denied",
            "severity": "HIGH",
            "error_type": "HTTP_403_FORBIDDEN",
            "plain_explanation": f"The web server is refusing to serve the page at {url} due to permission restrictions or firewall rules.",
            "root_cause": "Incorrect file permissions (e.g. not 644 for files / 755 for folders), missing index file, or ModSecurity / Web Application Firewall blocking requests.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Reset File & Directory Permissions in Hosting File Manager",
                    "action": "In your Hosting File Manager, set folder permissions to 755 and file permissions to 644 in public_html."
                },
                {
                    "step": 2,
                    "title": "Check Web Application Firewall / ModSecurity",
                    "action": "In cPanel > 'Security' > 'ModSecurity', check if any false-positive firewall rule is blocking traffic."
                }
            ],
            "support_ticket_template": f"""SUBJECT: 403 Forbidden error on www.auraxl.com

Dear Support Team,

Our website is showing a 403 Forbidden permission error on {url}. Could you please check the directory permissions and verify if any ModSecurity firewall rule is blocking requests?

Thank you."""
        }

    def _diagnose_dns(self, url: str, details: str) -> Dict[str, Any]:
        return {
            "title": "DNS Lookup Failed - Domain Not Resolving",
            "severity": "CRITICAL",
            "error_type": "DNS_RESOLUTION_FAILURE",
            "plain_explanation": f"The domain name '{url}' cannot be translated to a server IP address by DNS servers.",
            "root_cause": "Missing A/CNAME DNS records, domain registration expired, or nameservers misconfigured.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Check Domain Registration Status",
                    "action": "Log into your Domain Registrar (GoDaddy, Namecheap, Google Domains) and verify that the domain registration is active and not expired."
                },
                {
                    "step": 2,
                    "title": "Verify Nameservers & DNS 'A' Records",
                    "action": "In your DNS management panel, ensure you have an 'A' record pointing '@' to your server IP and a 'CNAME' record pointing 'www' to '@'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: DNS Resolution assistance for www.auraxl.com

Dear Registrar Support,

Our domain www.auraxl.com is failing DNS resolution. Please verify that the nameserver delegation and DNS zone records are properly configured.

Thank you."""
        }

    def _diagnose_slow_page(self, url: str, response_time_ms: float) -> Dict[str, Any]:
        return {
            "title": f"High Latency / Slow Page Load ({int(response_time_ms)}ms)",
            "severity": "WARNING",
            "error_type": "SLOW_PAGE_RESPONSE",
            "plain_explanation": f"The page at {url} took {int(response_time_ms)}ms to load, which exceeds the recommended 1500ms threshold.",
            "root_cause": "Uncached content, uncompressed large assets, unoptimized database queries, or server distance.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Enable Server-Level Caching & Cloudflare CDN",
                    "action": "Enable Cloudflare CDN caching or turn on Redis/LiteSpeed cache in your hosting control panel."
                },
                {
                    "step": 2,
                    "title": "Enable Gzip / Brotli Compression",
                    "action": "In cPanel > 'Optimize Website', select 'Compress All Content'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Server performance optimization for www.auraxl.com

Dear Support,

We are observing slow response times ({int(response_time_ms)}ms) on {url}. Could you please check if server caching (OPcache/Memcached) and Gzip compression are active for our account?

Thank you."""
        }

    def _diagnose_mixed_content(self, url: str, details: str) -> Dict[str, Any]:
        return {
            "title": "Insecure Mixed Content (HTTP assets on HTTPS page)",
            "severity": "WARNING",
            "error_type": "MIXED_CONTENT",
            "plain_explanation": f"Secure HTTPS page at {url} is loading images, scripts, or fonts via insecure http:// URLs, causing browser security warnings.",
            "root_cause": "Hardcoded http:// image or script URLs in the site theme or settings.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Enable 'Always Use HTTPS' and 'Automatic HTTPS Rewrites'",
                    "action": "In Cloudflare > 'SSL/TLS' > 'Edge Certificates', turn ON 'Always Use HTTPS' and 'Automatic HTTPS Rewrites'."
                },
                {
                    "step": 2,
                    "title": "Update Site URL in CMS Settings",
                    "action": "In your website settings / admin panel, verify that the WordPress Address and Site Address start with 'https://'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Enable HTTPS redirect & rewrites for www.auraxl.com

Dear Support,

Please ensure our hosting server enforces HTTPS redirection for all HTTP assets and pages.

Thank you."""
        }

    def _diagnose_security_headers(self, url: str, details: str) -> Dict[str, Any]:
        return {
            "title": "Missing Recommended Security Headers",
            "severity": "LOW",
            "error_type": "MISSING_SECURITY_HEADERS",
            "plain_explanation": f"The server is missing standard browser security headers (e.g. HSTS, X-Content-Type-Options, X-Frame-Options) on {url}.",
            "root_cause": "The web server or CDN proxy has not enabled HTTP Strict Transport Security (HSTS) or Clickjacking protection headers.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Enable HSTS in Cloudflare / Hosting Security Panel",
                    "action": "In Cloudflare > 'SSL/TLS' > 'Edge Certificates', scroll to 'HTTP Strict Transport Security (HSTS)' and click 'Enable'."
                },
                {
                    "step": 2,
                    "title": "Enable Security Headers via Control Panel",
                    "action": "In your hosting panel security settings or CMS security plugin (e.g. Wordfence/iThemes), enable 'Protect against Clickjacking' and 'X-Content-Type-Options'."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Security headers configuration for www.auraxl.com

Dear Support,

Could you please assist in enabling HSTS and X-Frame-Options headers on our web server configuration for www.auraxl.com?

Thank you."""
        }

    def _diagnose_broken_asset(self, url: str, details: str) -> Dict[str, Any]:
        return {
            "title": "Broken Asset or Image Link Detected",
            "severity": "MEDIUM",
            "error_type": "BROKEN_LINK_OR_ASSET",
            "plain_explanation": f"A resource or image referenced on {url} failed to load ({details}).",
            "root_cause": "The referenced image file or script was moved or deleted from the server.",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Re-upload the missing asset via Media Library or File Manager",
                    "action": "Log into your website admin / Media Library and re-upload the missing image or file."
                },
                {
                    "step": 2,
                    "title": "Update the Image Link in Page Editor",
                    "action": "Open the page editor and re-select the image from your media library."
                }
            ],
            "support_ticket_template": f"""SUBJECT: File upload / Media path check on www.auraxl.com

Dear Support,

We have an asset reporting a missing file error on {url}. Please verify that file permissions on the uploads/media directory are intact.

Thank you."""
        }

    def _diagnose_generic(self, url: str, error_type: str, details: str) -> Dict[str, Any]:
        return {
            "title": f"Site Anomaly Detected: {error_type}",
            "severity": "HIGH",
            "error_type": error_type,
            "plain_explanation": f"An issue was encountered while auditing {url}: {details}",
            "root_cause": f"The automated probe encountered an anomaly during inspection: {details}",
            "user_fix_steps": [
                {
                    "step": 1,
                    "title": "Check Hosting Server Status Page",
                    "action": "Visit your hosting provider's status page to check if there is an active maintenance window or server outage."
                },
                {
                    "step": 2,
                    "title": "Run a Manual Health Scan",
                    "action": "Use the 'Scan Now' button in the AuraXL Monitor dashboard to re-verify after checking your hosting panel."
                }
            ],
            "support_ticket_template": f"""SUBJECT: Website issue inquiry for www.auraxl.com

Dear Technical Support,

Our automated monitor detected an anomaly ({error_type}: {details}) on www.auraxl.com. Could you please inspect the server health and let us know if any action is needed?

Thank you."""
        }

    def chat_response(self, query: str, current_status: Dict[str, Any]) -> str:
        """
        Provides helpful, conversational answers to user queries regarding website status,
        diagnostics, hosting steps, and settings instructions without code.
        """
        q = query.lower()

        if "ssl" in q or "certificate" in q or "eof" in q or "protocol" in q:
            return (
                "🔒 **SSL / Connection Drop Diagnostic**\n\n"
                "**Current Status:** The server (IP: 34.120.137.41) is currently dropping incoming SSL/HTTPS connections (`SSL: UNEXPECTED_EOF_WHILE_READING`).\n\n"
                "**How to Fix (No Code Needed):**\n"
                "1. **Check Cloudflare / CDN:** If using Cloudflare, go to **SSL/TLS > Overview** and switch the mode to **Full** or **Flexible**.\n"
                "2. **Re-install Certificate:** In your cPanel or Hosting Dashboard, go to **SSL/TLS Status** and click **Run AutoSSL** or reinstall Let's Encrypt.\n"
                "3. **Contact Hosting Support:** Copy the pre-written support ticket from the **Diagnostics** tab and submit it to your host's support portal."
            )
        elif "fix" in q or "solution" in q or "how to" in q:
            return (
                "🛠️ **AuraXL Agentic Remediation Guide**\n\n"
                "All detected issues on `www.auraxl.com` have direct, non-code solutions:\n"
                "- **Step 1:** Open the **Diagnostics** tab in the bottom bar.\n"
                "- **Step 2:** Click **'View Solution'** on any active issue card.\n"
                "- **Step 3:** Follow the exact step-by-step settings checklist for your hosting panel/DNS.\n"
                "- **Step 4:** If the problem requires host intervention, click **'Copy Support Ticket'** to copy the formatted message and send it to your hosting provider's support team!"
            )
        elif "status" in q or "health" in q or "uptime" in q:
            score = current_status.get("health_score", 0)
            status_text = current_status.get("status", "UNKNOWN")
            issues_count = current_status.get("issues_count", 0)
            return (
                f"📊 **Current Website Health Report**\n\n"
                f"- **Target URL:** `www.auraxl.com`\n"
                f"- **Status:** `{status_text}`\n"
                f"- **Health Score:** **{score}/100**\n"
                f"- **Active Issues:** **{issues_count}**\n\n"
                "Tap **'Scan Now'** at any time to run an immediate deep crawl across all pages and sublinks."
            )
        elif "notification" in q or "alert" in q:
            return (
                "🔔 **Notification System Overview**\n\n"
                "- Push notifications and in-app sound/banner alerts are automatically sent when any page goes down or encounters an error.\n"
                "- You can manage alert sensitivity and intervals in the **Settings** tab."
            )
        else:
            return (
                f"🤖 **AuraXL AI Agent:** I am actively monitoring `www.auraxl.com`.\n\n"
                "You can ask me about:\n"
                "- *'Why is my SSL failing?'*\n"
                "- *'How do I fix the 34.120.137.41 connection error?'*\n"
                "- *'What is the current health status?'*\n"
                "- *'How to contact hosting support?'*\n\n"
                "Let me know what you need assistance with!"
            )

agent_engine = AgenticAIEngine()
