from mitmproxy import http
import re
import requests
import sqlite3
import time
import os
import telebot

# ------------- CONFIG -------------
AGE_SERVICE_URL = "http://127.0.0.1:5001/status"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "PARENT_CHAT_ID"
DB_PATH = os.path.expanduser("~/.peekshield_logs.db")
BLOCKED_DOMAINS = [
    r"pornhub\.com", r"xvideos\.com", r"xnxx\.com", r"redtube\.com"
]
BLOCKED_REGEX = [re.compile(pat, re.IGNORECASE) for pat in BLOCKED_DOMAINS]
ALERT_THROTTLE_SECONDS = 10

# init telegram bot (optional, safe to leave placeholders)
bot = None
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
except Exception:
    bot = None

# ------------- DB helpers -------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        url TEXT,
        host TEXT,
        is_minor INTEGER,
        age_estimate TEXT,
        note TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()
last_alert_time = 0

def log_event(url, host, is_minor, age_estimate, note="blocked"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO events (timestamp, url, host, is_minor, age_estimate, note) VALUES (?, ?, ?, ?, ?, ?)",
                (time.strftime("%Y-%m-%d %H:%M:%S"), url, host, int(is_minor), str(age_estimate), note))
    conn.commit()
    conn.close()

def send_telegram_alert(url, host, is_minor, age_estimate):
    global last_alert_time
    if bot is None:
        print("Telegram bot not configured.")
        return
    if time.time() - last_alert_time < ALERT_THROTTLE_SECONDS:
        return
    last_alert_time = time.time()
    text = f"PeekShield Alert!\nMinor detected accessing blocked site.\nHost: {host}\nURL: {url}\nAge estimate: {age_estimate}"
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text)
    except Exception as e:
        print("Telegram send error:", e)

# ------------- Utilities -------------
def is_blocked(hostname, url):
    # check host and full url parts
    for rx in BLOCKED_REGEX:
        if rx.search(hostname):
            return True
        if rx.search(url):
            return True
    return False

def get_age_status():
    try:
        r = requests.get(AGE_SERVICE_URL, timeout=0.5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("Age service error:", e)
    return {"is_minor": False, "age_estimate": None}

# ------------- mitmproxy hook -------------
def request(flow: http.HTTPFlow) -> None:
    host = flow.request.host
    full_url = flow.request.pretty_url

    # ignore local and mitmproxy websocket traffic
    if host in ("127.0.0.1", "localhost"):
        return

    if not is_blocked(host, full_url):
        return

    status = get_age_status()
    is_minor = status.get("is_minor", False)
    age_est = status.get("age_estimate", None)

    if is_minor:
        log_event(full_url, host, is_minor, age_est, note="blocked_by_policy")
        send_telegram_alert(full_url, host, is_minor, age_est)

        html = f"""<html><body style="font-family: sans-serif; text-align:center; padding:40px;">
        <h2>PeekShield — Access Blocked</h2>
        <p>Access to this site has been blocked for users under 16.</p>
        <p>Site: {host}</p>
        </body></html>"""
        flow.response = http.Response.make(403, html.encode("utf-8"), {"Content-Type": "text/html"})