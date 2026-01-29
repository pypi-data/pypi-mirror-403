"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import sqlite3
import requests
import re
from concurrent.futures import ThreadPoolExecutor
from src.constants import DB_PATH



class WebhookManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._setup_db()
        # Thread pool for non-blocking HTTP calls
        # Adjust max_workers based on server capacity
        self.executor = ThreadPoolExecutor(max_workers=20)

    def _setup_db(self):
        """Initialize SQLite tables for webhooks and subscriptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table: Webhooks (Stores endpoint and owner)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                api_key TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                failures INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Table: Subscriptions (Many-to-Many: Webhook <-> Currency)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                webhook_id INTEGER NOT NULL,
                currency_code TEXT NOT NULL,
                FOREIGN KEY(webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE,
                UNIQUE(webhook_id, currency_code)
            )
        """
        )

        # Index for fast lookup during alert processing
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sub_currency 
            ON subscriptions (currency_code)
        """
        )

        conn.commit()
        conn.close()

    def register_webhook(self, url: str, email: str, api_key: str, currencies: list):
        """
        Registers or updates a webhook subscription.
        """
        # 1. Basic Validation
        if not re.match(r"^https?://", url):
            raise ValueError("Invalid URL schema. Must be http or https.")
        if "@" not in email:
            raise ValueError("Invalid email address.")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 2. Upsert Webhook
            cursor.execute(
                """
                INSERT INTO webhooks (url, email,api_key, is_active, failures) 
                VALUES (?, ?, ?, 1, 0)
                ON CONFLICT(url) DO UPDATE SET 
                    email=excluded.email, 
                    is_active=1, 
                    failures=0
            """,
                (url, email, api_key),
            )

            # Get ID (either new or existing)
            cursor.execute("SELECT id FROM webhooks WHERE url = ?", (url,))
            webhook_id = cursor.fetchone()[0]

            # 3. Update Subscriptions
            # Remove old ones
            cursor.execute(
                "DELETE FROM subscriptions WHERE webhook_id = ?", (webhook_id,)
            )

            # Add new ones
            subs = [(webhook_id, code.upper()) for code in currencies]
            cursor.executemany(
                "INSERT INTO subscriptions (webhook_id, currency_code) VALUES (?, ?)",
                subs,
            )

            conn.commit()
            print(f"Webhook registered: {url} watching {len(currencies)} currencies")
        except Exception as e:
            print(f"Failed to register webhook: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _send_payload(self, url, alerts):
        """Actual HTTP Sender (runs in thread)"""
        try:
            # Short timeout to fail fast
            response = requests.post(
                url,
                json={
                    "event": "currency_alert",
                    "alerts": alerts,
                    "timestamp": alerts[0]["time"] if alerts else None,
                },
                timeout=3,
            )

            if response.status_code >= 400:
                self._record_failure(url)
                print(f"Webhook failed [{response.status_code}]: {url}")
            else:
                # Optional: Reset failure count on success
                pass

        except requests.exceptions.RequestException:
            self._record_failure(url)
            print(f"Webhook timeout/error: {url}")

    def _record_failure(self, url):
        """Increment failure count, disable if too many"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            UPDATE webhooks 
            SET failures = failures + 1,
                is_active = CASE WHEN failures >= 10 THEN 0 ELSE is_active END
            WHERE url = ?
        """,
            (url,),
        )
        conn.commit()
        conn.close()

    def process_alerts(self, alerts_list: list):
        """
        Main entry point.
        1. Maps alerts to subscribed webhooks.
        2. Groups data per webhook.
        3. Sends requests in parallel.
        """
        if not alerts_list:
            return

        # 1. Create a lookup map: Symbol -> Alert Object
        # Dictionary structure from manager.py assumed to have 'symbol' key
        alert_map = {alert["symbol"]: alert for alert in alerts_list}
        triggered_symbols = list(alert_map.keys())


        if not triggered_symbols:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 2. Optimized Query: Get all active URLs interested in these currencies
        placeholders = ",".join(["?"] * len(triggered_symbols))
        query = f"""
            SELECT w.url, s.currency_code 
            FROM webhooks w
            JOIN subscriptions s ON w.id = s.webhook_id
            WHERE w.is_active = 1 
            AND s.currency_code IN ({placeholders})
        """

        cursor.execute(query, triggered_symbols)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return

        # 3. Grouping: { "http://url.com": [alert_obj_1, alert_obj_2] }
        payloads = {}
        for url, currency in rows:
            if url not in payloads:
                payloads[url] = []

            # Add the specific alert object for this currency
            if currency in alert_map:
                payloads[url].append(alert_map[currency])

        # 4. Dispatch using ThreadPool
        print(f">> Dispatching alerts to {len(payloads)} webhooks...")
        for url, grouped_alerts in payloads.items():
            self.executor.submit(self._send_payload, url, grouped_alerts)


# --- Quick Test / Seeder if run directly ---
if __name__ == "__main__":
    wm = WebhookManager()
    # Seed a test webhook
    wm.register_webhook(
        "https://webhook.site/YOUR-TEST-ID", "admin@example.com", ["ADA", "EUR", "BTC"]
    )
