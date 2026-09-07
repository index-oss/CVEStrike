import os
import re
from daimport os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# === Load Secrets from .env ===
load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "openai/gpt-3.5-turbo")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")

# === Scheduler Setup ===
scheduler = BackgroundScheduler()

# === Helper: Clean HTML Tags ===
def clean_html(raw_html):
    if not raw_html:
        return "No Content"
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

# === 1. Fetch CISA News (Updated Feed URL) ===
def fetch_cyber_news():
    try:
        url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"[❌ Error fetching CISA feed: HTTP {response.status_code}]"

        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        feed = ""
        for item in items[:5]:
            title = item.find("title")
            desc = item.find("description")

            title_text = title.text.strip() if title is not None and title.text else "No Title"
            desc_text = clean_html(desc.text) if desc is not None and desc.text else "No Description"

            feed += f"🔸 Title: {title_text}\nSummary: {desc_text[:300]}...\n\n"
        return feed.strip()
    except Exception as e:
        return f"[❌ XML Parse Error] {e}"

# === 2. Analyze with LLM (OpenRouter) ===
def analyze_with_model(text):
    if not API_KEY:
        return text
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an offensive security researcher. Provide a concise bulleted threat summary focusing on CVEs, technical impact, and mitigation. Keep formatting clean for Telegram."
                },
                {"role": "user", "content": text}
            ]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
        res_json = res.json()
        
        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            return f"[❌ AI API Error] {res_json}"
    except Exception as e:
        return f"[❌ AI Connection Exception] {e}"

# === 3. Send Telegram Alert ===
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Skipping Telegram: Token or Chat ID missing in .env")
        return
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 *CVEStrike Threat Intel - {datetime.now().strftime('%d %b %Y')}*\n\n{message}",
            "parse_mode": "Markdown"
        }
        res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload, timeout=10)
        if res.status_code != 200:
            print(f"[!] Telegram failure: {res.text}")
        else:
            print("[+] Telegram alert sent successfully.")
    except Exception as e:
        print(f"[❌ Telegram Error] {e}")

# === 4. Send Pushbullet Alert ===
def send_pushbullet(message):
    if not PUSHBULLET_TOKEN:
        return
    try:
        requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"},
            json={"type": "note", "title": "CVEStrike Cyber Alert", "body": message[:4000]},
            timeout=10
        )
    except Exception as e:
        print(f"[❌ Pushbullet Error] {e}")

# === Core Pipeline Runner ===
def run_cvestrike_pipeline(trigger_label="Manual"):
    print(f"\n[⏰ {datetime.now().strftime('%H:%M:%S')}] Executing CVEStrike Pipeline ({trigger_label})...")
    raw_feed = fetch_cyber_news()
    if raw_feed.startswith("[❌"):
        print(raw_feed)
    else:
        print("[✔️ CISA Feed Pulled]")
        summary = analyze_with_model(raw_feed)
        print("[✔️ LLM Analysis Complete]")
        send_telegram(summary)
        send_pushbullet(summary)
        print("✅ Alerts dispatched successfully.")

# === Schedule Cron Jobs (10:45 AM & 5:30 PM IST) ===
scheduler.add_job(
    run_cvestrike_pipeline,
    CronTrigger(hour=10, minute=45, timezone="Asia/Kolkata"),
    args=["Morning 10:45 AM Trigger"],
    id="morning_cve_job"
)

scheduler.add_job(
    run_cvestrike_pipeline,
    CronTrigger(hour=17, minute=30, timezone="Asia/Kolkata"),
    args=["Evening 05:30 PM Trigger"],
    id="evening_cve_job"
)

# === FastAPI Lifespan Handler ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not scheduler.running:
        scheduler.start()
        print("[*] CVEStrike Scheduler started successfully.")
    yield
    if scheduler.running:
        scheduler.shutdown()
        print("[*] CVEStrike Scheduler stopped cleanly.")

app = FastAPI(title="CVEStrike Engine", version="2.0", lifespan=lifespan)

# === Routes ===

@app.get("/health")
def health_ping():
    """UptimeRobot ping endpoint to prevent cloud sleep"""
    return {
        "status": "healthy",
        "service": "CVEStrike Engine",
        "system_time": datetime.now().isoformat()
    }

@app.post("/trigger-now")
def manual_trigger():
    """Manual pipeline execution endpoint"""
    run_cvestrike_pipeline("Manual Route Trigger")
    return {"status": "Pipeline execution completed."}

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Built-in Web Control Panel"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CVEStrike Control Center</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; text-align: center; }
            .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 30px; max-width: 500px; margin: auto; }
            h1 { color: #58a6ff; margin-bottom: 5px; }
            button { background: #238636; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 6px; cursor: pointer; margin-top: 20px; }
            button:hover { background: #2ea043; }
            .info { margin-top: 20px; font-size: 14px; color: #8b949e; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡️ CVEStrike Engine</h1>
            <p>Vulnerability Research & Automated Alert Center</p>
            <button onclick="triggerAlert()">⚡ Send Instant Alert Now</button>
            <div id="status" class="info"></div>
            <hr style="border-color: #30363d; margin-top: 25px;">
            <p class="info">⏰ Daily Broadcasts: <b>10:45 AM</b> & <b>05:30 PM IST</b></p>
            <p class="info">💚 Keep-Alive Endpoint: <code>/health</code></p>
        </div>
        <script>
            function triggerAlert() {
                document.getElementById('status').innerText = 'Triggering alert pipeline...';
                fetch('/trigger-now', { method: 'POST' })
                    .then(res => res.json())
                    .then(data => { document.getElementById('status').innerText = '✅ Alert Sent!'; })
                    .catch(err => { document.getElementById('status').innerText = '❌ Error executing trigger'; });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)tetime import datetime
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# === Load Secrets from .env ===
load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "openai/gpt-3.5-turbo")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")

# === Scheduler Setup ===
scheduler = BackgroundScheduler()

# === Helper: Clean HTML Tags ===
def clean_html(raw_html):
    if not raw_html:
        return "No Content"
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

# === 1. Fetch CISA News (Updated Feed URL) ===
def fetch_cyber_news():
    try:
        url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"[❌ Error fetching CISA feed: HTTP {response.status_code}]"

        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        feed = ""
        for item in items[:5]:
            title = item.find("title")
            desc = item.find("description")

            title_text = title.text.strip() if title is not None and title.text else "No Title"
            desc_text = clean_html(desc.text) if desc is not None and desc.text else "No Description"

            feed += f"🔸 Title: {title_text}\nSummary: {desc_text[:300]}...\n\n"
        return feed.strip()
    except Exception as e:
        return f"[❌ XML Parse Error] {e}"

# === 2. Analyze with LLM (OpenRouter) ===
def analyze_with_model(text):
    if not API_KEY:
        return text
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an offensive security researcher. Provide a concise bulleted threat summary focusing on CVEs, technical impact, and mitigation. Keep formatting clean for Telegram."
                },
                {"role": "user", "content": text}
            ]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
        res_json = res.json()
        
        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            return f"[❌ AI API Error] {res_json}"
    except Exception as e:
        return f"[❌ AI Connection Exception] {e}"

# === 3. Send Telegram Alert ===
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Skipping Telegram: Token or Chat ID missing in .env")
        return
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 *CVEStrike Threat Intel - {datetime.now().strftime('%d %b %Y')}*\n\n{message}",
            "parse_mode": "Markdown"
        }
        res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload, timeout=10)
        if res.status_code != 200:
            print(f"[!] Telegram failure: {res.text}")
        else:
            print("[+] Telegram alert sent successfully.")
    except Exception as e:
        print(f"[❌ Telegram Error] {e}")

# === 4. Send Pushbullet Alert ===
def send_pushbullet(message):
    if not PUSHBULLET_TOKEN:
        return
    try:
        requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"},
            json={"type": "note", "title": "CVEStrike Cyber Alert", "body": message[:4000]},
            timeout=10
        )
    except Exception as e:
        print(f"[❌ Pushbullet Error] {e}")

# === Core Pipeline Runner ===
def run_cvestrike_pipeline(trigger_label="Manual"):
    print(f"\n[⏰ {datetime.now().strftime('%H:%M:%S')}] Executing CVEStrike Pipeline ({trigger_label})...")
    raw_feed = fetch_cyber_news()
    if raw_feed.startswith("[❌"):
        print(raw_feed)
    else:
        print("[✔️ CISA Feed Pulled]")
        summary = analyze_with_model(raw_feed)
        print("[✔️ LLM Analysis Complete]")
        send_telegram(summary)
        send_pushbullet(summary)
        print("✅ Alerts dispatched successfully.")

# === Schedule Cron Jobs (10:45 AM & 5:30 PM IST) ===
scheduler.add_job(
    run_cvestrike_pipeline,
    CronTrigger(hour=10, minute=45, timezone="Asia/Kolkata"),
    args=["Morning 10:45 AM Trigger"],
    id="morning_cve_job"
)

scheduler.add_job(
    run_cvestrike_pipeline,
    CronTrigger(hour=17, minute=30, timezone="Asia/Kolkata"),
    args=["Evening 05:30 PM Trigger"],
    id="evening_cve_job"
)

# === FastAPI Lifespan Handler ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not scheduler.running:
        scheduler.start()
        print("[*] CVEStrike Scheduler started successfully.")
    yield
    if scheduler.running:
        scheduler.shutdown()
        print("[*] CVEStrike Scheduler stopped cleanly.")

app = FastAPI(title="CVEStrike Engine", version="2.0", lifespan=lifespan)

# === Routes ===

@app.get("/health")
def health_ping():
    """UptimeRobot ping endpoint to prevent cloud sleep"""
    return {
        "status": "healthy",
        "service": "CVEStrike Engine",
        "system_time": datetime.now().isoformat()
    }

@app.post("/trigger-now")
def manual_trigger():
    """Manual pipeline execution endpoint"""
    run_cvestrike_pipeline("Manual Route Trigger")
    return {"status": "Pipeline execution completed."}

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Built-in Web Control Panel"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CVEStrike Control Center</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; text-align: center; }
            .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 30px; max-width: 500px; margin: auto; }
            h1 { color: #58a6ff; margin-bottom: 5px; }
            button { background: #238636; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 6px; cursor: pointer; margin-top: 20px; }
            button:hover { background: #2ea043; }
            .info { margin-top: 20px; font-size: 14px; color: #8b949e; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡️ CVEStrike Engine</h1>
            <p>Vulnerability Research & Automated Alert Center</p>
            <button onclick="triggerAlert()">⚡ Send Instant Alert Now</button>
            <div id="status" class="info"></div>
            <hr style="border-color: #30363d; margin-top: 25px;">
            <p class="info">⏰ Daily Broadcasts: <b>10:45 AM</b> & <b>05:30 PM IST</b></p>
            <p class="info">💚 Keep-Alive Endpoint: <code>/health</code></p>
        </div>
        <script>
            function triggerAlert() {
                document.getElementById('status').innerText = 'Triggering alert pipeline...';
                fetch('/trigger-now', { method: 'POST' })
                    .then(res => res.json())
                    .then(data => { document.getElementById('status').innerText = '✅ Alert Sent!'; })
                    .catch(err => { document.getElementById('status').innerText = '❌ Error executing trigger'; });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
