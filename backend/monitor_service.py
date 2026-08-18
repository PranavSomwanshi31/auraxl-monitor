import threading
import time
from datetime import datetime
from typing import Optional
from crawler import WebsiteCrawler
from storage import get_setting, add_notification

class BackgroundMonitorService:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_scanning = False
        self.last_scan_time: Optional[datetime] = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            print("[AuraXL Monitor] Background monitoring service started.")

    def stop(self):
        with self._lock:
            self._running = False

    def is_active(self) -> bool:
        return self._running

    def is_currently_scanning(self) -> bool:
        return self._is_scanning

    def trigger_instant_scan(self) -> dict:
        """Trigger an on-demand audit in background or synchronously"""
        target_url = get_setting("target_url", "https://www.auraxl.com")
        self._is_scanning = True
        try:
            crawler = WebsiteCrawler(target_url=target_url)
            summary = crawler.run_full_audit()
            self.last_scan_time = datetime.now()
            return summary
        finally:
            self._is_scanning = False

    def _run_loop(self):
        # Initial scan on startup
        time.sleep(2)
        try:
            self.trigger_instant_scan()
        except Exception as e:
            print(f"[AuraXL Monitor] Initial scan error: {e}")

        while self._running:
            try:
                interval_min_str = get_setting("monitor_interval_minutes", "5")
                try:
                    interval_sec = max(60, int(interval_min_str) * 60)
                except ValueError:
                    interval_sec = 300

                auto_enabled = get_setting("auto_monitor_enabled", "true").lower() == "true"

                if auto_enabled:
                    target_url = get_setting("target_url", "https://www.auraxl.com")
                    self._is_scanning = True
                    try:
                        crawler = WebsiteCrawler(target_url=target_url)
                        crawler.run_full_audit()
                        self.last_scan_time = datetime.now()
                    finally:
                        self._is_scanning = False

                # Sleep in small slices to respond promptly to stop
                for _ in range(int(interval_sec / 5)):
                    if not self._running:
                        break
                    time.sleep(5)

            except Exception as e:
                print(f"[AuraXL Monitor] Monitor loop error: {e}")
                time.sleep(10)

monitor_service = BackgroundMonitorService()
