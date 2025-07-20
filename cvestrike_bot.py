import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
import os

# === Load Secrets ===
load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")

# === Fetch CISA News ===
def fetch_cyber_news():
    try:
        url = "https://www.cisa.gov/sites/default/files/feeds/alerts.xml"
        response = requests.get(url)
        if response.status_code != 200:
            return "[❌ Error fetching CISA feed]"

        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        feed = ""
        for item in items[:5]:
            title = item.find("title")
            desc = item.find("description")

            title_text = title.text.strip() if title is not None and title.text else "No Title"
            desc_text = desc.text.strip() if desc is not None and desc.text else "No Description"

            feed += f"🔸 *{title_text}*\n{desc_text}\n\n"
        return feed.strip()
    except Exception as e:
        return f"[❌ XML Parse Error] {e}"

# === Analyze with LLM ===
def analyze_with_model(text):
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a cybersecurity analyst. Summarize key threat intel from this feed."},
                {"role": "user", "content": text}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[❌ AI Error] {e}"

# === Telegram ===
def send_telegram(message):
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 *Cyber Threat Summary - {datetime.now().strftime('%d %b %Y')}*\n\n{message}",
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print(f"[❌ Telegram Error] {e}")

# === Pushbullet ===
def send_pushbullet(message):
    try:
        requests.post("https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"},
            json={"type": "note", "title": "Cyber Alert", "body": message[:4000]}
        )
    except Exception as e:
        print(f"[❌ Pushbullet Error] {e}")

# === Main ===
if __name__ == "__main__":
    print(f"[⏰ {datetime.now().strftime('%H:%M:%S')}] Launching CVESTRIKE Intel Bot...")
    raw_feed = fetch_cyber_news()
    if raw_feed.startswith("[❌"):
        print(raw_feed)
    else:
        print("[✔️ Feed Fetched]")
        summary = analyze_with_model(raw_feed)
        print("[✔️ Summary Ready]\n", summary[:300], "...")
        send_telegram(summary)
        send_pushbullet(summary)
        print("✅ Alerts sent.")
