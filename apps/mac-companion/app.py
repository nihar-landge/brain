import rumps
import threading
import time
import requests
import os
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Load Environment Variables from .env file
load_dotenv()

API_URL = os.getenv("BRAIN_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("BRAIN_API_KEY", "")

# Default Headers
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

class BrainCompanionApp(rumps.App):
    def __init__(self):
        super(BrainCompanionApp, self).__init__("🧠", quit_button="Quit Brain Companion")
        
        # Menu Items
        self.status_item = rumps.MenuItem("Status: Waiting...")
        self.start_timer_item = rumps.MenuItem("Start Deep Work", callback=self.start_deep_work)
        self.stop_timer_item = rumps.MenuItem("Stop Deep Work", callback=self.stop_deep_work)
        self.settings_item = rumps.MenuItem("Preferences", callback=self.open_preferences)
        
        # Add to menu
        self.menu = [
            self.status_item,
            rumps.separator,
            self.start_timer_item,
            self.stop_timer_item,
            rumps.separator,
            self.settings_item
        ]
        
        # State
        self.is_running = True
        self.last_nudge_count = 0
        
        # Start Background Thread
        self.thread = threading.Thread(target=self.poll_backend)
        self.thread.daemon = True
        self.thread.start()

    def start_deep_work(self, sender):
        try:
            # Tell backend to start a deep work session
            rumps.notification("Brain Companion", "Deep Work", "Started a new deep work session!")
            self.title = "🧠 💻"
        except Exception as e:
            rumps.notification("Error", "Could not start session", str(e))

    def stop_deep_work(self, sender):
        try:
            # Tell backend to stop deep work session
            rumps.notification("Brain Companion", "Deep Work", "Stopped deep work session.")
            self.title = "🧠"
        except Exception as e:
            rumps.notification("Error", "Could not stop session", str(e))

    def open_preferences(self, sender):
        global API_KEY, HEADERS
        window = rumps.Window(
            message="Enter your API Key:",
            title="Brain Companion Settings",
            default_text=API_KEY,
            dimensions=(300, 20)
        )
        response = window.run()
        if response.clicked:
            API_KEY = response.text
            HEADERS["X-API-Key"] = API_KEY
            # Optionally save to a .env file locally here

    def poll_backend(self):
        """Poll the FastAPI backend for active nudges and anomalies every 30 seconds."""
        while self.is_running:
            try:
                # 1. Fetch Nudges
                res = requests.get(f"{API_URL}/api/nudges", headers=HEADERS, timeout=5)
                if res.status_code == 200:
                    nudges = res.json().get("nudges", [])
                    active_nudges = [n for n in nudges if n.get("is_active")]
                    
                    if len(active_nudges) > self.last_nudge_count:
                        # We have a NEW active nudge
                        new_nudge = active_nudges[-1]
                        rumps.notification("🧠 Brain Nudge", new_nudge.get("title", "New Nudge"), new_nudge.get("message", ""))
                    
                    self.last_nudge_count = len(active_nudges)
                    self.status_item.title = f"Status: OK ({len(active_nudges)} active nudges)"
                elif res.status_code in (401, 403):
                    self.status_item.title = "Status: Invalid API Key"
                else:
                    self.status_item.title = f"Status: Server Error ({res.status_code})"
                
            except RequestException:
                self.status_item.title = "Status: Disconnected"
            
            time.sleep(30)

if __name__ == "__main__":
    if not API_KEY:
        print("WARNING: BRAIN_API_KEY environment variable not set. API calls will fail.")
    app = BrainCompanionApp()
    app.run()
