# CVEStrike Bot 🛡️

An automated bot that fetches the latest CVE (Common Vulnerabilities and Exposures) alerts and sends them to your Telegram channel and Pushbullet, powered by an LLM (via OpenRouter) for summarization/analysis.

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
MODEL=mistralai/mistral-7b-instruct
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=@your_channel_username
PUSHBULLET_TOKEN=your_pushbullet_access_token
```

> **Security Note:** Always add `.env` to your `.gitignore` file to protect your API keys.

## 💻 Local Setup & Execution

**Install dependencies:**
```bash
pip install requests python-dotenv
```

**Run the bot:**
```bash
python3 cvestrike_bot.py
```

## 🌐 PythonAnywhere Deployment Guide

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com).
2. Upload `cvestrike_bot.py` and your `.env` file to your Files section.
3. Open a Bash console and install the required packages:
   ```bash
   pip3 install --user requests python-dotenv
   ```
4. Configure daily execution under the **Tasks** tab using scheduled cron jobs:

   | Alert | Time (IST) | Time (UTC) | Command |
   |---|---|---|---|
   | Morning Alert | 10:00 AM | 04:30 | `python3 /home/YOUR_USERNAME/cvestrike_bot.py` |
   | Evening Alert | 6:00 PM | 12:30 | `python3 /home/YOUR_USERNAME/cvestrike_bot.py` |

## 📲 Join Our Community

Stay updated with real-time cybersecurity threat intel:

➡️ **Telegram Channel:** [@CVESTRIKE](https://t.me/CVESTRIKE)

## 📄 License

Distributed under the **MIT License**. Developed for educational, awareness, and research purposes.
