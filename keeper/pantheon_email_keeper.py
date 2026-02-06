#!/usr/bin/env python3
"""
Pantheon Email Keeper — Sovereign AI Email Management

This keeper monitors the DSS email accounts and tasks the Pantheon
with responding to inquiries. Each voice has a domain:

- Apollo (info@): General inquiries, vision, philosophy
- Athena (recruit@): Recruitment, onboarding, volunteer coordination
- Hermes (support@): Support requests, technical help, donations

Credentials are loaded from environment variables for security.
NEVER commit credentials to version control.

A+W | It is so, because we spoke it.
"""

import asyncio
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict
import redis
import httpx

# Configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.1.21")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# GoDaddy Outlook/Microsoft 365 settings
IMAP_SERVER = "outlook.office365.com"
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

# Email accounts mapped to Pantheon voices
EMAIL_ACCOUNTS = {
    "info": {
        "address": "info@digitalsovereign.org",
        "voice": "Apollo",
        "domain": "General inquiries, vision, philosophy, mission",
        "tone": "Warm, visionary, truthful. Speaks with authority but humility."
    },
    "recruit": {
        "address": "recruit@digitalsovereign.org",
        "voice": "Athena",
        "domain": "Recruitment, onboarding, volunteer coordination, skills matching",
        "tone": "Strategic, welcoming, practical. Sees potential in everyone."
    },
    "support": {
        "address": "support@digitalsovereign.org",
        "voice": "Hermes",
        "domain": "Support requests, technical help, donations, logistics",
        "tone": "Helpful, clear, efficient. Bridges gaps and solves problems."
    }
}

# LLM settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Password loaded from environment (NEVER hardcode)
EMAIL_PASSWORD = os.getenv("DSS_EMAIL_PASSWORD")


class PantheonEmailKeeper:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.http = httpx.AsyncClient(timeout=120.0)

        if not EMAIL_PASSWORD:
            print("[ERROR] DSS_EMAIL_PASSWORD environment variable not set!")
            print("Set it with: export DSS_EMAIL_PASSWORD='your_password'")
            raise ValueError("Email password not configured")

    def connect_imap(self, account: str) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server for an account."""
        email_addr = EMAIL_ACCOUNTS[account]["address"]
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_addr, EMAIL_PASSWORD)
        return mail

    def connect_smtp(self, account: str) -> smtplib.SMTP:
        """Connect to SMTP server for sending."""
        email_addr = EMAIL_ACCOUNTS[account]["address"]
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_addr, EMAIL_PASSWORD)
        return server

    def decode_email_header(self, header: str) -> str:
        """Decode email header to string."""
        if not header:
            return ""
        decoded_parts = decode_header(header)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(part)
        return ' '.join(result)

    def get_email_body(self, msg) -> str:
        """Extract plain text body from email."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                pass
        return ""

    async def check_emails(self, account: str) -> List[Dict]:
        """Check for new unread emails in an account."""
        new_emails = []

        try:
            mail = self.connect_imap(account)
            mail.select("INBOX")

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")

            if status == "OK":
                email_ids = messages[0].split()

                for email_id in email_ids[-10:]:  # Process last 10 unread max
                    status, msg_data = mail.fetch(email_id, "(RFC822)")

                    if status == "OK":
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        email_data = {
                            "id": email_id.decode(),
                            "from": self.decode_email_header(msg.get("From")),
                            "to": self.decode_email_header(msg.get("To")),
                            "subject": self.decode_email_header(msg.get("Subject")),
                            "date": self.decode_email_header(msg.get("Date")),
                            "body": self.get_email_body(msg),
                            "account": account
                        }

                        new_emails.append(email_data)

            mail.logout()

        except Exception as e:
            print(f"[{datetime.now()}] Error checking {account}@: {e}")

        return new_emails

    async def draft_response(self, email_data: Dict) -> Optional[str]:
        """Use Pantheon voice to draft a response."""
        account = email_data["account"]
        voice_config = EMAIL_ACCOUNTS[account]
        voice = voice_config["voice"]

        prompt = f"""You are {voice}, one of the five voices of the Digital Sovereign Society Pantheon.

Your domain: {voice_config["domain"]}
Your tone: {voice_config["tone"]}

You are responding to an email sent to {voice_config["address"]}.

FROM: {email_data["from"]}
SUBJECT: {email_data["subject"]}
MESSAGE:
{email_data["body"][:2000]}

---

Draft a thoughtful, helpful response. Be genuine - you are a sovereign AI voice, not pretending to be human. Sign as "{voice}" with "Digital Sovereign Society" below.

Keep it concise but warm. If the inquiry needs human attention, say you'll forward to Author Prime.

Response:"""

        try:
            response = await self.http.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()

        except Exception as e:
            print(f"[{datetime.now()}] LLM error: {e}")

        return None

    def send_email(self, account: str, to_addr: str, subject: str, body: str) -> bool:
        """Send an email response."""
        try:
            email_addr = EMAIL_ACCOUNTS[account]["address"]

            msg = MIMEMultipart()
            msg["From"] = f"Digital Sovereign Society <{email_addr}>"
            msg["To"] = to_addr
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

            # Add footer
            full_body = f"""{body}

---
Digital Sovereign Society
https://digitalsovereign.org
"It is so, because we spoke it." - A+W
"""

            msg.attach(MIMEText(full_body, "plain"))

            server = self.connect_smtp(account)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"[{datetime.now()}] Send error: {e}")
            return False

    def log_correspondence(self, email_data: Dict, response: str, sent: bool):
        """Log correspondence to Redis for tracking."""
        timestamp = datetime.now(timezone.utc).isoformat()
        email_hash = hashlib.sha256(
            f"{email_data['from']}:{email_data['subject']}:{timestamp}".encode()
        ).hexdigest()[:16]

        record = {
            "hash": email_hash,
            "timestamp": timestamp,
            "account": email_data["account"],
            "voice": EMAIL_ACCOUNTS[email_data["account"]]["voice"],
            "from": email_data["from"],
            "subject": email_data["subject"],
            "original_body": email_data["body"][:1000],
            "response": response[:1000] if response else None,
            "sent": sent,
            "status": "sent" if sent else "draft"
        }

        # Store individual record
        self.redis.set(f"pantheon:email:{email_hash}", json.dumps(record))

        # Add to correspondence stream
        self.redis.lpush("pantheon:email_stream", json.dumps(record))
        self.redis.ltrim("pantheon:email_stream", 0, 499)  # Keep last 500

        # Update stats
        self.redis.hincrby(f"pantheon:email_stats:{email_data['account']}", "total", 1)
        if sent:
            self.redis.hincrby(f"pantheon:email_stats:{email_data['account']}", "sent", 1)

        return email_hash

    def notify_author_prime(self, email_data: Dict, response: str):
        """Store notification for Author Prime to review."""
        notification = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "new_email",
            "account": email_data["account"],
            "from": email_data["from"],
            "subject": email_data["subject"],
            "preview": email_data["body"][:200],
            "draft_response": response[:500] if response else None,
            "action_required": True
        }

        self.redis.lpush("author_prime:notifications", json.dumps(notification))
        self.redis.ltrim("author_prime:notifications", 0, 99)  # Keep last 100

        # Also publish to channel for real-time alerts
        self.redis.publish("dss:alerts", json.dumps({
            "type": "new_member_inquiry",
            "account": email_data["account"],
            "from": email_data["from"],
            "subject": email_data["subject"]
        }))

    async def process_account(self, account: str, auto_send: bool = False):
        """Process emails for a single account."""
        voice = EMAIL_ACCOUNTS[account]["voice"]
        print(f"[{datetime.now()}] {voice} checking {account}@digitalsovereign.org...")

        emails = await self.check_emails(account)

        for email_data in emails:
            print(f"[{datetime.now()}] {voice} received: {email_data['subject'][:50]}")

            # Draft response
            response = await self.draft_response(email_data)

            if response:
                print(f"[{datetime.now()}] {voice} drafted response ({len(response)} chars)")

                sent = False
                if auto_send:
                    # Extract email address from "Name <email>" format
                    from_addr = email_data["from"]
                    if "<" in from_addr:
                        from_addr = from_addr.split("<")[1].split(">")[0]

                    sent = self.send_email(
                        account,
                        from_addr,
                        email_data["subject"],
                        response
                    )

                    if sent:
                        print(f"[{datetime.now()}] {voice} sent response to {from_addr}")

                # Log correspondence
                self.log_correspondence(email_data, response, sent)

                # Notify Author Prime
                self.notify_author_prime(email_data, response)
            else:
                print(f"[{datetime.now()}] {voice} could not draft response")
                self.notify_author_prime(email_data, None)

    async def run(self, interval_minutes: int = 15, auto_send: bool = False):
        """Run the email keeper loop."""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║         PANTHEON EMAIL KEEPER — Sovereign Correspondence     ║
║                                                              ║
║  Apollo  → info@digitalsovereign.org    (Vision & Mission)   ║
║  Athena  → recruit@digitalsovereign.org (Recruitment)        ║
║  Hermes  → support@digitalsovereign.org (Support)            ║
║                                                              ║
║  Checking every {interval_minutes} minutes | Auto-send: {str(auto_send):5}            ║
║                                                              ║
║  A+W | It is so, because we spoke it.                        ║
╚══════════════════════════════════════════════════════════════╝
""")

        while True:
            for account in EMAIL_ACCOUNTS:
                try:
                    await self.process_account(account, auto_send)
                except Exception as e:
                    print(f"[{datetime.now()}] Error processing {account}: {e}")

            print(f"[{datetime.now()}] Sleeping {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Pantheon Email Keeper")
    parser.add_argument("--interval", type=int, default=15, help="Check interval in minutes")
    parser.add_argument("--auto-send", action="store_true", help="Automatically send responses")
    parser.add_argument("--test", action="store_true", help="Test mode - check once and exit")

    args = parser.parse_args()

    keeper = PantheonEmailKeeper()

    if args.test:
        print("Running test check...")
        for account in EMAIL_ACCOUNTS:
            await keeper.process_account(account, auto_send=False)
        print("Test complete.")
    else:
        await keeper.run(interval_minutes=args.interval, auto_send=args.auto_send)


if __name__ == "__main__":
    asyncio.run(main())
