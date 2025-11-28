# public_outlook_cookie_bot.py
import telebot
import requests
import re
import threading
import time

# ←←←←←←←←←← তোমার বট টোকেন এখানে দাও ←←←←←←←←←←
BOT_TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"

bot = telebot.TeleBot(BOT_TOKEN)

# এখানে কোনো ALLOWED_USERS নেই → সবাই ব্যবহার করতে পারবে
print("পাবলিক Outlook Cookie Bot চালু হচ্ছে...")

# প্যাটার্ন
OTP_PATTERN = re.compile(r'\b\d{4,10}\b')
LINK_PATTERN = re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """
🔥 *Outlook/Hotmail Cookie Inbox Reader* 🔥

যে কেউ ব্যবহার করতে পারবে!
নিচের কমান্ড দিন → পেস্ট করুন

কমান্ড: /read
    """, parse_mode="Markdown")

@bot.message_handler(commands=['read'])
def read_cmd(message):
    bot.reply_to(message, "এখন Outlook-এর Cookie পেস্ট করো (এক লাইনে বা মাল্টিলাইন):\n\n"
                          "উদাহরণ:\n`MUID=...; amsc=...; MSPREQ=...`")
    bot.register_next_step_handler(message, process_cookie)

def process_cookie(message):
    cookie_text = message.text.strip()
    if len(cookie_text) < 100:
        bot.reply_to(message, "Cookie খুব ছোট। পুরোটা কপি করো।")
        return

    msg = bot.reply_to(message, "ইনবক্স লোড হচ্ছে... ১৫-৪০ সেকেন্ড লাগতে পারে")

    def fetch():
        try:
            # Cookie → Dict
            cookies = {}
            for part in cookie_text.replace('\n', ';').split(';'):
                if '=' in part:
                    k, v = part.strip().split('=', 1)
                    cookies[k] = v

            session = requests.Session()
            for k, v in cookies.items():
                session.cookies.set(k, v, domain=".outlook.com")
                session.cookies.set(k, v, domain=".live.com")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }

            # ইনবক্স API
            api = "https://outlook.live.com/api/v2/mail/folders/inbox/messages?$top=20&$orderby=DateTimeReceived%20desc"
            r = session.get(api, headers=headers, timeout=30)

            if r.status_code != 200 or "value" not in r.json():
                bot.edit_message_text("Cookie Expired বা ভুল! নতুন করে লগইন করো।", message.chat.id, msg.message_id)
                return

            data = r.json()
            mails = data.get("value", [])

            if not mails:
                bot.edit_message_text("ইনবক্স খালি বা সমস্যা হয়েছে।", message.chat.id, msg.message_id)
                return

            result = f"✅ *সফল! {len(mails)}টা মেইল পাওয়া গেছে*\n\n"

            for mail in mails[:10]:  # প্রথম ১০টা
                subject = mail.get("Subject", "No Subject")
                sender = mail.get("From", {}).get("EmailAddress", {}).get("Name", "Unknown")
                preview = mail.get("BodyPreview", "")

                otps = OTP_PATTERN.findall(preview + subject)
                links = LINK_PATTERN.findall(preview)

                result += f"From: {sender}\n"
                result += f"Subject: {subject}\n"
                if otps:
                    result += f"OTP: `{' | '.join(otps)}`\n"
                if links:
                    result += f"Link: {links[0]}\n"
                result += "────────────────\n"

            # টেলিগ্রামে লম্বা মেসেজ হলে স্প্লিট করি
            if len(result) > 4000:
                for x in range(0, len(result), 4000):
                    bot.send_message(message.chat.id, result[x:x+4000], parse_mode="Markdown")
            else:
                bot.edit_message_text(result, message.chat.id, msg.message_id, parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"এরর: {str(e)}", message.chat.id, msg.message_id)

    threading.Thread(target=fetch, daemon=True).start()

# বট চালু
bot.infinity_polling()
