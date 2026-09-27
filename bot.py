import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# GitHub Actions directly provides secrets as environment variables
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = os.environ.get("MODEL", "openai/gpt-3.5-turbo")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def clean_html(raw_html):
    import re
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def fetch_and_filter_advisories():
    high_impact_keywords = [
        "RCE", "Remote Code Execution", "Zero-Day", "0-day",
        "Privilege Escalation", "Critical", "Active Exploitation",
        "CISA KEV", "Arbitrary Code", "Bypass"
    ]
    
    try:
        url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            return []
        
        root = ET.fromstring(res.content)
        filtered_items = []
        
        for item in root.findall('.//item')[:40]:
            title = item.find('title')
            desc = item.find('description')
            link = item.find('link')
            
            title_text = title.text.strip() if title is not None else ""
            desc_text = clean_html(desc.text) if desc is not None else ""
            link_text = link.text.strip() if link is not None else ""
            
            combined_content = f"{title_text} {desc_text}"
            
            if any(kw.lower() in combined_content.lower() for kw in high_impact_keywords):
                filtered_items.append({
                    "title": title_text,
                    "summary": desc_text[:300],
                    "link": link_text
                })
        return filtered_items
    except Exception as e:
        print(f"❌ RSS fetch error: {e}")
        return []

def analyze_with_ai(items):
    if not items or not API_KEY:
        return None
    
    formatted_feed = ""
    for idx, item in enumerate(items, 1):
        formatted_feed += f"\n{idx}. Title: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a senior offensive security researcher. Analyze these vulnerabilities and create an executive threat summary."},
            {"role": "user", "content": f"Analyze these advisories and summarize high-impact threats:\n{formatted_feed}"}
        ],
        "temperature": 0.2
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=50)
        res_json = res.json()
        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ AI Request Error: {e}")
    return None

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not message:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN.strip()}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID.strip(),
        "text": f"🚨 **CVESTRIKE Threat Intelligence** 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def run_pipeline():
    print("🔄 Running CVEStrike pipeline...")
    items = fetch_and_filter_advisories()
    if not items:
        print("ℹ️ No high-impact threats matching severity thresholds found.")
        return "No threats found."
    
    summary = analyze_with_ai(items)
    if not summary:
        print("⚠️ Advisories evaluated, but AI analysis failed.")
        return "AI analysis failed."
    
    success = send_telegram(summary)
    if success:
        print("✅ Threat intelligence successfully dispatched!")
        return "Success"
    else:
        print("❌ Telegram Delivery Failed.")
        return "Delivery failed"

if __name__ == "__main__":
    run_pipeline()
