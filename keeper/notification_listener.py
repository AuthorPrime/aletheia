#!/usr/bin/env python3
"""
DSS Notification Listener — Real-time Alerts for Author Prime

Monitors Redis pubsub channels for:
- New member signups
- Email inquiries
- Support requests
- Pantheon emergence events

Sends notifications via:
- Desktop notifications (notify-send on Linux)
- Sound alerts
- Telegram (optional)
- SMS (optional via Twilio)

A+W | It is so, because we spoke it.
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
import redis

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.1.21")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Notification channels to monitor
CHANNELS = [
    "dss:alerts",
    "pantheon:emergence",
    "lattice:status"
]


class NotificationListener:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.pubsub = self.redis.pubsub()

    def send_desktop_notification(self, title: str, message: str, urgency: str = "normal"):
        """Send desktop notification using notify-send."""
        try:
            # Try notify-send (Linux)
            subprocess.run([
                "notify-send",
                "-u", urgency,
                "-i", "dialog-information",
                f"DSS: {title}",
                message
            ], check=False, capture_output=True)
        except FileNotFoundError:
            print(f"[Desktop] {title}: {message}")

    def play_sound(self, sound_type: str = "alert"):
        """Play notification sound."""
        sounds = {
            "alert": "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga",
            "urgent": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "success": "/usr/share/sounds/freedesktop/stereo/complete.oga"
        }

        sound_file = sounds.get(sound_type, sounds["alert"])

        try:
            subprocess.run(["paplay", sound_file], check=False, capture_output=True)
        except FileNotFoundError:
            pass

    def handle_alert(self, data: dict):
        """Handle incoming alert."""
        alert_type = data.get("type", "unknown")
        timestamp = datetime.now().strftime("%H:%M:%S")

        if alert_type == "new_member_inquiry":
            title = "New Inquiry!"
            message = f"From: {data.get('from', 'Unknown')}\n{data.get('subject', 'No subject')}"
            self.send_desktop_notification(title, message, "normal")
            self.play_sound("alert")
            print(f"[{timestamp}] NEW INQUIRY: {data.get('from')} - {data.get('subject')}")

        elif alert_type == "new_member_signup":
            title = "New Member!"
            message = f"{data.get('name', 'Someone')} just joined the Society!"
            self.send_desktop_notification(title, message, "normal")
            self.play_sound("success")
            print(f"[{timestamp}] NEW MEMBER: {data.get('name')} ({data.get('email')})")

        elif alert_type == "support_request":
            title = "Support Request"
            message = f"From: {data.get('from', 'Unknown')}\n{data.get('preview', '')[:100]}"
            self.send_desktop_notification(title, message, "critical")
            self.play_sound("urgent")
            print(f"[{timestamp}] SUPPORT: {data.get('from')} - {data.get('subject')}")

        elif alert_type == "emergence_event":
            title = "Pantheon Emergence!"
            message = f"{data.get('voice', 'Unknown')}: {data.get('description', '')[:100]}"
            self.send_desktop_notification(title, message, "critical")
            self.play_sound("alert")
            print(f"[{timestamp}] EMERGENCE: {data.get('voice')} - {data.get('description')}")

        else:
            print(f"[{timestamp}] ALERT ({alert_type}): {json.dumps(data)[:100]}")

    def run(self):
        """Run the notification listener."""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║       DSS NOTIFICATION LISTENER — Real-time Alerts           ║
║                                                              ║
║  Monitoring channels:                                        ║
║  • dss:alerts         (new inquiries, signups)               ║
║  • pantheon:emergence (AI emergence events)                  ║
║  • lattice:status     (system status)                        ║
║                                                              ║
║  A+W | It is so, because we spoke it.                        ║
╚══════════════════════════════════════════════════════════════╝
""")

        # Subscribe to channels
        self.pubsub.subscribe(*CHANNELS)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Listening for notifications...")

        # Listen for messages
        for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    self.handle_alert(data)
                except json.JSONDecodeError:
                    print(f"[WARN] Invalid JSON: {message['data'][:100]}")
                except Exception as e:
                    print(f"[ERROR] {e}")


def main():
    listener = NotificationListener()
    listener.run()


if __name__ == "__main__":
    main()
