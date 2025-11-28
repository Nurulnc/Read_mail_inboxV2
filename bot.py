# outlook_cookie_bot.py
import telebot
import requests
import re
import json
import threading

# ←←←←←←←←←← তোমার বট টোকেন দাও ←←←←←←←←←←
BOT_TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"

bot = telebot.TeleBot(BOT_TOKEN)

# শুধু তুমি আর তোমার ফ্রেন্ডরা ব্যবহার করতে পারবে
ALLOWED_USERS = [1651695602]  # ← তোমার Telegram ID দাও (int)

# OTP + Link প্যাটার্ন
OTP_PATTERN = re.compile(r'\b\d{4,10}\b')
LINK_PATTERN = re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)')

def is_allowed(user_id):
    return user_id in ALLOWED_USERS

@bot.message_handler(commands=['start'])
def start(message):
    if not is_allowed(message.from_user.id):
        bot.reply_to(message, "অনুমতি নেই।")
        return
    bot.reply_to(message, """
🔥 *Outlook Cookie Inbox Reader* 🔥

শুধু তোমার Outlook-এর Cookie পেস্ট করো → পুরো ইনবক্স + OTP বের হয়ে আসবে!

কমান্ড:
/cookie

তারপর Cookie পেস্ট করো (browser থেকে নিয়ে)

⚠️ শুধু প্রাইভেট ব্যবহার। কখনো পাবলিক করো না।
    """, parse_mode="Markdown")

@bot.message_handler(commands=['cookie'])
def cookie_cmd(message):
    if not is_allowed(message.from_user.id):
        return
    bot.reply_to(message, "Outlook-এর Cookie পেস্ট করো (এক লাইনে বা মাল্টিলাইন):\n\n"
                          "উদাহরণ:\n`MUID=...; c_c=...; MSP...`")
    bot.register_next_step_handler(message, process_cookie)

def process_cookie(message):
    if not is_allowed(message.from_user.id):
        return

    cookie_text = message.text.strip()
    if not cookie_text or len(cookie_text) < 50:
        bot.reply_to(message, "ভুল Cookie। আবার চেষ্টা করো।")
        return

    bot.reply_to(message, "Cookie পেয়েছি! ইনবক্স লোড হচ্ছে... ১০-২০ সেকেন্ড লাগবে")

    def fetch_inbox():
        try:
            # Cookie কে ডিকশনারিতে কনভার্ট
            cookies = {}
            for line in cookie_text.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    cookies[key.strip()] = value.strip()

            session = requests.Session()
            for k, v in cookies.items():
                session.cookies.set(k, v, domain=".outlook.com")
                session.cookies.set(k, v, domain=".live.com")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://outlook.live.com/"
            }

            # ইনবক্স JSON এন্ডপয়েন্ট
            url = "https://outlook.live.com/mail/0/inbox"
            response = session.get(url, headers=headers, timeout=20)

            if "Sign in" in response.text or response.status_code != 200:
                bot.reply_to(message, "Cookie এক্সপায়ার্ড বা ভুল। নতুন করে লগইন করো।")
                return

            # API থেকে মেইল লিস্ট
            api_url = "https://outlook.live.com/api/v2/mail/folders/inbox/messages?$top=15&$orderby=DateTimeReceived desc"
            resp = session.get(api_url, headers=headers)
            data = resp.json()

            result = f"✅ *লগইন সফল!* ({len(data.get('value', []))}টা মেইল পাওয়া গেছে)\n\n"

            for mail in data.get("value", []):
                subject = mail.get("Subject", "No Subject")
                sender = mail.get("From", {}).get("EmailAddress", {}).get("Name", "Unknown")
                body_preview = mail.get("BodyPreview", "")

                # OTP + Link খুঁজি
                otp = OTP_PATTERN.findall(body_preview + subject)
                link = LINK_PATTERN.findall(body_preview)

                result += f"From: {sender}\n"
                result += f"Subject: {subject}\n"
                if otp:
                    result += f"OTP: `{' | '.join(otp)}`\n"
                if link:
                    result += f"Link: {link[0]}\n"
                result += "────────────────\n"

                if len(result) > 3800:
                    result += "\n... আরো মেইল আছে"
                    break

            bot.reply_to(message, result if result else "ইনবক্স খালি!", parse_mode="Markdown")

        except Exception as e:
            bot.reply_to(message, f"এরর: {str(e)}\n\nCookie ভুল বা এক্সপায়ার্ড।")

    threading.Thread(target=fetch_inbox, daemon=True).start()

# বট চালু
print("Outlook Cookie Bot চালু হয়েছে...")
bot.infinity_polling()
