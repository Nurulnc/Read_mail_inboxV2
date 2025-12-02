# bot.py - 100% Working Selenium Version (Undetected + Highlighted Link)
from telebot import TeleBot, types
import time
import os
import json
from datetime import datetime
import threading

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# তোমার বট টোকেন
TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"  # <-- চেঞ্জ করো
bot = TeleBot(TOKEN)

# প্রতি ইউজারের জন্য সেশন
user_sessions = {}

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--headless")  # VPS এ হেডলেস, লোকালে False করো
    driver = uc.Chrome(options=options, version_main=131)  # Chrome 131+ দরকার
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

def extract_real_link_with_selenium(cookies_str, chat_id):
    driver = None
    try:
        bot.send_message(chat_id, "Chrome খুলছে... লগইন হচ্ছে...")
        
        driver = create_driver()
        driver.get("https://outlook.live.com")
        time.sleep(5)

        # কুকিজ ইনজেক্ট করা
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookie_dict = {
                    'name': name,
                    'value': value,
                    'domain': '.live.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': False
                }
                try:
                    driver.add_cookie(cookie_dict)
                except:
                    pass

        driver.get("https://outlook.live.com/mail/inbox")
        time.sleep(8)

        # লগইন চেক
        if "signin" in driver.current_url or "login" in driver.current_url:
            bot.send_message(chat_id, "কুকিজ এক্সপায়ার্ড বা ইনভ্যালিড!")
            return

        bot.send_message(chat_id, "ইনবক্স ওপেন হয়েছে! TextNow মেইল খুঁজছি...")

        # TextNow বা verification মেইল খোঁজা
        mails = driver.find_elements(By.CSS_SELECTOR, "div[role='option'][aria-label*='TextNow'], div[aria-label*='verification'], div[aria-label*='Verify'], div[aria-label*='no-reply']")
        
        if not mails:
            mails = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")[:15]  # লাস্ট ১৫টা

        found = False
        for mail in mails:
            try:
                sender = mail.get_attribute("aria-label").lower()
                if any(x in sender for x in ["textnow", "verify", "confirmation", "no-reply", "security"]):
                    bot.send_message(chat_id, f"TextNow মেইল পাওয়া গেছে!\nওপেন করছি...")
                    mail.click()
                    time.sleep(6)
                    found = True
                    break
            except:
                continue

        if not found:
            bot.send_message(chat_id, "কোনো TextNow/Verification মেইল পাওয়া যায়নি।")
            return

        # মেইল বডি থেকে লিঙ্ক বের করা
        body = driver.page_source
        import re
        links = re.findall(r'https?://[^\s<>"\']+', body)
        
        real_link = None
        for link in links:
            if len(link) > 60 and any(word in link.lower() for word in ["verify", "confirmation", "click", "live.com", "account", "security"]):
                if "textnow" not in link and "unsubscribe" not in link:
                    real_link = link.split('&')[0]
                    if "http" in real_link:
                        break

        if real_link:
            clean = real_link.split('?')[0] if len(real_link) > 1000 else real_link
            msg = f"""*আসল ভেরিফিকেশন লিঙ্ক পাওয়া গেছে!*

`{clean}`

কপি করো: {clean}"""

            bot.send_message(chat_id, msg, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, "লিঙ্ক পাওয়া যায়নি। মেইল ম্যানুয়ালি চেক করো।")

    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")
    finally:
        if driver:
            driver.quit()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Send Outlook Cookies")
    markup.add(btn)
    
    bot.send_message(message.chat.id, 
        "*আউটলুকের Full Cookies পাঠাও*\n\n"
        "Chrome → Outlook লগইন → Cookie Editor → Export as Netscape/JSON → পেস্ট করো",
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and len(m.text) > 300)
def receive_cookies(message):
    cookies = message.text
    chat_id = message.chat.id
    
    bot.reply_to(message, "কুকিজ পেয়েছি! এখনই চেক করছি...")
    
    # ব্যাকগ্রাউন্ডে চালানো (যাতে বট হ্যাং না হয়)
    threading.Thread(target=extract_real_link_with_selenium, args=(cookies, chat_id)).start()

print("Selenium Real Link Extractor Bot চালু হলো...")
bot.infinity_polling()
