# bot.py - 100% Working on Thegsmwork Free Hosting (No Selenium)
from telebot import TeleBot, types
import requests
import re
import json
import time
from bs4 import BeautifulSoup

# তোমার বট টোকেন এখানে বসাও
TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"  # ← চেঞ্জ করো
bot = TeleBot(TOKEN)

def extract_link_from_cookies(cookies_str):
    try:
        session = requests.Session()
        
        # কুকিজ লোড করা
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                session.cookies.set(name, value, domain='.outlook.com')
                session.cookies.set(name, value, domain='.live.com')

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # ইনবক্স ওপেন
        inbox = session.get("https://outlook.live.com/mail/inbox", headers=headers, timeout=20)
        
        if "sign" in inbox.text.lower() or inbox.status_code != 200:
            return "কুকিজ এক্সপায়ার্ড বা ইনভ্যালিড!"

        soup = BeautifulSoup(inbox.text, 'html.parser')
        
        # সব মেইলের লিস্ট
        mails = soup.find_all("div", {"role": "option"})[:25]

        for mail in mails:
            sender_text = mail.get("aria-label", "").lower()
            if any(x in sender_text for x in ["textnow", "verify", "no-reply", "confirmation"]):
                # এই মেইলের ভিতরে লিঙ্ক খুঁজি
                body_text = str(mail) + inbox.text
                links = re.findall(r'https?://[^\s<>"\']+', body_text)
                
                for link in links:
                    l = link.lower()
                    if len(link) > 60 and any(k in l for k in ["verify", "confirm", "click", "account.live.com", "microsoft.com"]):
                        if "unsubscribe" not in l and "textnow" not in l:
                            clean = link.split('&')[0]
                            return f"""আসল ভেরিফিকেশন লিঙ্ক পাওয়া গেছে!

`{clean}`

কপি করো → {clean}"""

        return "TextNow মেইল পাওয়া গেছে কিন্তু লিঙ্ক পাওয়া যায়নি।"

    except Exception as e:
        return f"এরর: {str(e)}"

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Send Outlook Cookies")
    bot.send_message(m.chat.id,
        "*আউটলুক Full Cookies পাঠাও*\n\n"
        "Chrome → Login → Cookie Editor → Export → পেস্ট করো\n"
        "TextNow থেকে আসল লিঙ্ক বের করে দিব",
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and len(m.text) > 400)
def get_cookies(m):
    bot.reply_to(m, "কুকিজ পেয়েছি! লিঙ্ক বের করছি...")
    time.sleep(2)
    result = extract_link_from_cookies(m.text)
    bot.send_message(m.chat.id, result, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def all(m):
    bot.reply_to(m, "কুকিজ পাঠাও বা /start দাও")

print("Bot চালু হলো – Free Hosting Ready!")
bot.infinity_polling()
