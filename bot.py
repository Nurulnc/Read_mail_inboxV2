# bot.py - Termux এ 100% Working | Headless | Real Outlook Link Extractor
from telebot import TeleBot, types
import time
import threading
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

# তোমার বট টোকেন এখানে বসাও
TOKEN = "8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw"  # ← চেঞ্জ করো

bot = TeleBot(TOKEN)

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")  # নতুন হেডলেস মোড
    options.add_argument("--no-zygote")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-tools")
    
    driver = uc.Chrome(options=options, version_main=131)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        window.navigator.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    })
    return driver

def extract_link(cookies, chat_id):
    driver = None
    try:
        bot.send_message(chat_id, "Chrome চালু হচ্ছে... (হেডলেস মোড)")
        driver = get_driver()
        
        driver.get("https://outlook.live.com")
        time.sleep(6)

        # কুকিজ লোড
        for cookie in cookies.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                try:
                    driver.add_cookie({'name': name, 'value': value, 'domain': '.live.com'})
                except:
                    pass
        
        driver.get("https://outlook.live.com/mail/inbox")
        time.sleep(10)

        if "login" in driver.current_url or "signin" in driver.current_url:
            bot.send_message(chat_id, "কুকিজ এক্সপায়ার্ড বা ভুল!")
            return

        bot.send_message(chat_id, "ইনবক্স ওপেন হয়েছে! TextNow মেইল খুঁজছি...")

        # সর্বশেষ ২০টা মেইল চেক
        mails = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")[:20]
        
        found = False
        for mail in mails:
            try:
                label = mail.get_attribute("aria-label") or ""
                if any(k in label.lower() for k in ["textnow", "verify", "confirmation", "no-reply", "security"]):
                    bot.send_message(chat_id, "TextNow মেইল পাওয়া গেছে! ওপেন করছি...")
                    mail.click()
                    time.sleep(7)
                    found = True
                    break
            except:
                continue

        if not found:
            bot.send_message(chat_id, "কোনো TextNow মেইল পাওয়া যায়নি। নতুন করে চেক করো।")
            return

        # লিঙ্ক বের করা
        page = driver.page_source
        links = re.findall(r'https?://[^\s<>"\']+', page)
        
        real_link = None
        for link in links:
            l = link.lower()
            if len(link) > 60 and any(x in l for x in ["verify", "confirmation", "clickhere", "account", "live.com", "microsoft"]):
                if "unsubscribe" not in l and "textnow.com" not in l:
                    real_link = link.split('&')[0].split(' ')[0]
                    break

        if real_link:
            short = real_link[:2000] + ("..." if len(real_link) > 2000 else "")
            msg = f"""*আসল ভেরিফিকেশন লিঙ্ক পাওয়া গেছে!*

`{short}`

কপি করো → {real_link}"""

            bot.send_message(chat_id, msg, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, "লিঙ্ক পাওয়া যায়নি। মেইল ম্যানুয়ালি চেক করো।")

    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")
    finally:
        if driver:
            driver.quit()

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Send Outlook Cookies")
    bot.send_message(m.chat.id, 
        "*আউটলুকের Full Cookies পাঠাও*\n\n"
        "Chrome → Login → Cookie Editor → Export (Netscape) → পেস্ট করো",
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and ("cookie" in m.text.lower() or len(m.text) > 500))
def get_cookies(m):
    cookies = m.text
    bot.reply_to(m, "কুকিজ পেয়েছি! এখনই লিঙ্ক বের করছি...")
    threading.Thread(target=extract_link, args=(cookies, m.chat.id)).start()

@bot.message_handler(func=lambda m: True)
def all(m):
    bot.reply_to(m, "কুকিজ পাঠাও বা /start দাও")

print("Termux Real Outlook Bot চালু হলো...")
bot.infinity_polling()
