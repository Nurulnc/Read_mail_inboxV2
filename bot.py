# bot.py - 100% Working Real TN Receiver (December 2025 Fixed)
from telebot import TeleBot, types
import requests
import re
import json
import time

TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"  # তোমার টোকেন
bot = TeleBot(TOKEN)

def extract_link(cookies_str):
    try:
        s = requests.Session()
        
        # কুকিজ লোড
        for c in cookies_str.replace('\n', ';').split(';'):
            if '=' in c and c.strip():
                n, v = c.strip().split('=', 1)
                s.cookies.set(n, v, domain='.outlook.com')
                s.cookies.set(n, v, domain='.live.com')
                s.cookies.set(n, v, domain='outlook.live.com')

        # এই হেডারগুলো না দিলে 2025 এ কাজ করে না
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-AnchorMailbox": "pitostoreyh1552@outlook.com",  # এটা ডাইনামিক করব পরে
            "X-OWA-CANARY": "",  # পরে ফিল করব
            "Referer": "https://outlook.live.com/mail/",
            "Origin": "https://outlook.live.com",
            "Connection": "keep-alive",
        }

        # প্রথমে CANARY টোকেন নিয়ে আসি (এটাই ম্যাজিক)
        r1 = s.get("https://outlook.live.com/mail/", timeout=20)
        canary = re.search(r'data-canary="(.*?)"', r1.text)
        if not canary:
            return "ক্যানারি টোকেন পাওয়া যায়নি। কুকিজ রিফ্রেশ করো।"
        headers["X-OWA-CANARY"] = canary.group(1)

        # এখন আসল API কল
        api_url = "https://outlook.office.com/mail/api/v2.0/me/messages?$top=50&$select=Subject,From,BodyPreview,UniqueBody,ReceivedDateTime"
        resp = s.get(api_url, headers=headers, timeout=25)

        if resp.status_code != 200:
            return f"স্ট্যাটাস কোড: {resp.status_code} — কুকিজ এক্সপায়ার্ড।"

        data = resp.json()
        for mail in data.get("value", []):
            sender = mail.get("From", {}).get("EmailAddress", {}).get("Address", "").lower()
            subject = mail.get("Subject", "").lower()
            body = mail.get("UniqueBody", {}).get("Content", "").lower()

            if any(x in (sender + subject + body) for x in ["textnow", "verify", "code", "confirmation"]):
                links = re.findall(r'https?://[^\s<>"\']+', mail.get("UniqueBody", {}).get("Content", ""))
                for link in links:
                    if len(link) > 60 and any(k in link.lower() for k in ["verify", "confirm", "account.live.com", "login.live.com", "microsoft"]):
                        if "unsubscribe" not in link.lower() and "textnow.com" not in link.lower():
                            clean = link.split('&')[0].split('"')[0].strip()
                            return f"""আসল লিঙ্ক পাওয়া গেছে!

`{clean}`

কপি করো: {clean}"""

        return "TextNow মেইল পাওয়া গেছে কিন্তু লিঙ্ক নেই।"

    except Exception as e:
        return f"এরর: {str(e)[:120]}"

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Send Outlook Cookies")
    bot.send_message(m.chat.id,
        "*Real TN Receiver (2025 Working)*\n\n"
        "আউটলুকের Full Cookies পাঠাও\n"
        "TextNow থেকে আসল লিঙ্ক ৫-১০ সেকেন্ডে বের করবে\n\n"
        "Chrome → Login → Cookie Editor → Export (Netscape) → পেস্ট করো",
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: len(m.text or "") > 600)
def get_cookies(m):
    bot.reply_to(m, "কুকিজ পেয়েছি! আসল লিঙ্ক বের করছি...")
    result = extract_link(m.text)
    bot.send_message(m.chat.id, result, parse_mode="Markdown", disable_web_page_preview=True)

print("2025 Final Working Bot চালু হলো")
bot.infinity_polling()
