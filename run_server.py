import os
import sys
import webbrowser
import threading
import time
import socket

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_global_tunnel(port=5000):
    try:
        from pycloudflared import try_cloudflare
        print("  [*] Launching Secure Global HTTPS Tunnel (Cloudflare)...")
        tunnel = try_cloudflare(port=port)
        global_url = tunnel.tunnel
        
        # Save to file
        with open(os.path.join(os.path.dirname(__file__), "GLOBAL_ACCESS_URL.txt"), "w", encoding="utf-8") as f:
            f.write(global_url)
            
        print("\n" + "*"*65)
        print(f"  [+] GLOBAL ANYWHERE ACCESS URL (Worldwide HTTPS):")
        print(f"      👉 {global_url}")
        print("*"*65 + "\n")
        print(f"  --> Share or open this link on ANY phone, 4G/5G data, or remote PC!")
        print(f"  --> Android APK: Open in Chrome > Tap 'Install AuraXL Monitor'.\n")
    except Exception as e:
        print(f"  [-] Global Tunnel Notice: {e}")

if __name__ == "__main__":
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.append(backend_path)
    
    from app import app
    from monitor_service import monitor_service
    
    local_ip = get_local_ip()
    port = 5000
    
    # Start Background Crawler Monitor
    monitor_service.start()
    
    print("\n" + "="*65)
    print("  [+] AURAXL AGENTIC AI WEBSITE MONITOR & DIAGNOSTIC APK")
    print("="*65)
    print(f"  Local Web Access:    http://127.0.0.1:{port}")
    print(f"  Android Phone Link:  http://{local_ip}:{port}")
    print(f"  Default UserID:      admin")
    print(f"  Default Password:    AuraXL@2026")
    print(f"  Target Website:      https://www.auraxl.com")
    print("="*65)

    # Launch Global Tunnel in background
    tunnel_thread = threading.Thread(target=start_global_tunnel, args=(port,), daemon=True)
    tunnel_thread.start()

    def open_browser():
        time.sleep(2.0)
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            pass
        
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host="0.0.0.0", port=port, debug=False)
