

# CVESTRIKE Bot 🔐📡
A daily cybersecurity intelligence bot that:
- Fetches latest CISA security alerts
- Summarizes them using a local LLM via OpenRouter
- Sends formatted threat reports to Telegram & Pushbullet

---

## 🧠 Features
- CISA RSS Feed parsing (top threat intel)
- Secure LLM analysis (e.g. Mistral via OpenRouter)
- Telegram channel updates (Markdown formatted)
- Optional Pushbullet push notifications
- Fully automatable (PythonAnywhere scheduling supported)

---

## 🔐 Setup Secure Environment (.env)

Create a `.env` file in your project root directory:

OPENROUTER_API_KEY=your_openrouter_api_key MODEL=mistralai/mistral-7b-instruct TELEGRAM_TOKEN=your_telegram_bot_token TELEGRAM_CHAT_ID=@your_channel_username PUSHBULLET_TOKEN=your_pushbullet_access_token

**Important**: Add `.env` to `.gitignore` to avoid exposing your keys!

.env

---

## 💻 Run Locally

1. Install dependencies:
```bash
pip install requests python-dotenv

2. Run the bot:



python3 cvestrike_bot.py


---

🌐 Deploy on PythonAnywhere (Free Hosting)

1. nanywhere.com


2. Upload:

cvestrike_bot.py

.env



3. In the Bash Console, install required libraries:



pip3 install --user requests python-dotenv


---

⏰ Step 4: Schedule Cyber Alerts (Daily)

Go to the Tasks page on PythonAnywhere and schedule:

Morning Alert (10:00 AM IST → 04:30 UTC)

python3 /home/YOUR_USERNAME/cvestrike_bot.py

Evening Alert (6:00 PM IST → 12:30 UTC)

python3 /home/YOUR_USERNAME/cvestrike_bot.py

✅ You now have an automated threat intel bot!


---

📲 Join Our Channel

Stay ahead of cyber threats:

➡️ https://t.me/CVESTRIKE


---

📄 License

MIT License — for educational, awareness, and research purposes.
