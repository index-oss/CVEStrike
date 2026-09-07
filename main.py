import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import streamlit as st

# === Page Configuration ===
st.set_page_config(
    page_title="CVEStrike Control Center",
    page_icon="🛡️",
    layout="centered"
)

# === Load Keys (Streamlit Secrets or Environment Variables) ===
API_KEY = st.secrets.get("API_KEY") or os.getenv("API_KEY")
MODEL = st.secrets.get("MODEL") or os.getenv("MODEL", "openai/gpt-3.5-turbo")
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
PUSHBULLET_TOKEN = st.secrets.get("PUSHBULLET_TOKEN") or os.getenv("PUSHBULLET_TOKEN")

# === Helper: HTML Stripper ===
def clean_html(raw_html):
    if not raw_html:
        return "No Content"
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

# === 1. Fetch CISA Feed ===
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

# === 2. Analyze via OpenRouter LLM ===
def analyze_with_model(text):
    if not API_KEY:
        return text
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY.strip()}",
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
        return False, "Telegram Token or Chat ID missing."
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID.strip(),
            "text": f"🚨 *CVEStrike Threat Intel - {datetime.now().strftime('%d %b %Y')}*\n\n{message}",
            "parse_mode": "Markdown"
        }
        res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN.strip()}/sendMessage", json=payload, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

# === 4. Send Pushbullet Alert ===
def send_pushbullet(message):
    if not PUSHBULLET_TOKEN:
        return
    try:
        requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": PUSHBULLET_TOKEN.strip(), "Content-Type": "application/json"},
            json={"type": "note", "title": "CVEStrike Cyber Alert", "body": message[:4000]},
            timeout=10
        )
    except Exception as e:
        print(f"[❌ Pushbullet Error] {e}")

# === Streamlit Control Panel Interface ===
st.title("🛡️ CVEStrike Engine")
st.caption("Automated Vulnerability Research & Threat Intel Center")

st.divider()

if st.button("⚡ Send Instant Alert Now", type="primary", use_container_width=True):
    with st.spinner("Executing pipeline: Fetching CISA Feed & Generating LLM Summary..."):
        raw_feed = fetch_cyber_news()
        
        if raw_feed.startswith("[❌"):
            st.error(raw_feed)
        else:
            summary = analyze_with_model(raw_feed)
            
            st.subheader("Generated Threat Intel:")
            st.info(summary)
            
            success, response_msg = send_telegram(summary)
            send_pushbullet(summary)
            
            if success:
                st.success("✅ Threat alert successfully dispatched to Telegram!")
            else:
                st.error(f"❌ Telegram Error: {response_msg}")

st.divider()
st.markdown("⏰ **Scheduled Timings (When deployed as Daemon):** `10:45 AM` & `05:30 PM IST`")
