import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import streamlit as st

# === Page Configuration ===
st.set_page_config(
    page_title="CVEStrike Control Center",
    page_icon="🛡️",import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
import streamlit as st

# === Page Config ===
st.set_page_config(page_title="CVEStrike Engine", page_icon="🛡️", layout="centered")

# === Fetch Secrets ===
API_KEY = st.secrets.get("API_KEY") or os.getenv("API_KEY")
MODEL = st.secrets.get("MODEL") or os.getenv("MODEL", "openai/gpt-3.5-turbo")
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

# === HTML Cleaner ===
def clean_html(raw_html):
    if not raw_html:
        return ""
    return re.sub(r'<.*?>', '', raw_html).strip()

# === 1. Fetch & High-Impact Filtering ===
def fetch_and_filter_advisories():
    high_impact_keywords = [
        "RCE", "Remote Code Execution", "Zero-Day", "0-day", "Unauthenticated",
        "Privilege Escalation", "Critical", "Active Exploitation", "CISA KEV",
        "Arbitrary Code", "Bypass", "Heap Overflow"
    ]

    try:
        url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=12)
        
        if res.status_code != 200:
            return []

        root = ET.fromstring(res.content)
        filtered_items = []

        for item in root.findall(".//item")[:10]:
            title = item.find("title")
            desc = item.find("description")
            link = item.find("link")

            title_text = title.text.strip() if title is not None and title.text else "No Title"
            desc_text = clean_html(desc.text) if desc is not None and desc.text else ""
            link_text = link.text.strip() if link is not None and link.text else ""

            combined_content = f"{title_text} {desc_text}"

            # High Severity Keyword Check
            if any(re.search(rf"\b{re.escape(kw)}\b", combined_content, re.I) for kw in high_impact_keywords):
                filtered_items.append({
                    "title": title_text,
                    "summary": desc_text[:500],
                    "link": link_text
                })

        return filtered_items
    except Exception as e:
        print(f"[❌ XML Fetch Error]: {e}")
        return []

# === 2. AI Threat Analysis & False Positive Filter ===
def analyze_with_ai(items):
    if not items or not API_KEY:
        return None

    formatted_feed = ""
    for idx, item in enumerate(items, 1):
        formatted_feed += f"{idx}. Title: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are a senior offensive security researcher and vulnerability analyst. "
            "Filter out noise, low-impact advisories, and routine patches. "
            "Focus strictly on high-severity vulnerabilities, active zero-days, RCEs, and critical infrastructure threats. "
            "Output clear, actionable threat intelligence formatted in Markdown for Telegram broadcast. "
            "Include CVE IDs, Severity, Impact, and Actionable Mitigation where available."
        )

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze these advisories and summarize high-impact threats:\n\n{formatted_feed}"}
            ],
            "temperature": 0.2
        }

        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res_json = res.json()

        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[❌ AI Request Error]: {e}")
    
    return None

# === 3. Telegram Dispatch ===
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not message:
        return False, "Missing Token/ChatID or Empty Message."

    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID.strip(),
            "text": f"🔥 *CVEStrike Threat Intelligence Alert*\n_{datetime.now().strftime('%d %b %Y | %H:%M IST')}_\n\n{message}",
            "parse_mode": "Markdown"
        }
        res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN.strip()}/sendMessage", json=payload, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

# === Core Execution Pipeline ===
def run_pipeline():
    items = fetch_and_filter_advisories()
    if not items:
        return "No high-impact threats matching severity thresholds."

    summary = analyze_with_ai(items)
    if not summary:
        return "Advisories evaluated, but none passed strict high-severity filtering."

    success, msg = send_telegram(summary)
    if success:
        return "✅ Threat intelligence summary successfully dispatched to Telegram."
    return f"❌ Telegram Delivery Failed: {msg}"

# === Streamlit Dashboard Interface ===
st.title("🛡️ CVEStrike Engine Pro")
st.caption("Offensive Security & Automated Threat Intelligence System")

st.divider()

col1, col2 = st.columns(2)
col1.metric("Filter Engine", "Zero-Day & RCE Focus")
col2.metric("Automation", "GitHub Actions / Scheduled")

st.divider()

if st.button("⚡ Run Threat Pipeline Sync", type="primary", use_container_width=True):
    with st.spinner("Processing CISA feed & executing LLM threat analysis..."):
        status = run_pipeline()
        st.info(status)
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
