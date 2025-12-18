import telebot
import imaplib
import email
import re
from email.header import decode_header

API_TOKEN = '8369983599:AAFq8R8qXplog8UOVUdBCqb4MP-Lrn3ufIw'
bot = telebot.TeleBot(API_TOKEN)

def get_otp_and_links(body):
    # ৫ থেকে ৮ ডিজিটের OTP খোঁজার জন্য
    otp_pattern = r'\b\d{4,8}\b'
    # লিঙ্ক খোঁজার জন্য
    link_pattern = r'(https?://[^\s]+)'
    
    otps = re.findall(otp_pattern, body)
    links = re.findall(link_pattern, body)
    return otps, links

@bot.message_handler(commands=['start', 'get_otp'])
def send_welcome(message):
    bot.reply_to(message, "📥 আপনার ইমেইল ডেটা দিন।\nফরম্যাট: `email|password`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: "|" in message.text)
def handle_mail(message):
    try:
        user_data = message.text.split("|")
        email_user = user_data[0].strip()
        email_pass = user_data[1].strip()

        bot.send_message(message.chat.id, "🔄 ইনবক্স চেক করা হচ্ছে...")

        # Outlook/Hotmail IMAP সংযোগ
        mail = imaplib.IMAP4_SSL("imap-mail.outlook.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # সর্বশেষ ইমেইলটি খুঁজে বের করা
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()
        
        if not mail_ids:
            bot.send_message(message.chat.id, "❌ ইনবক্সে কোনো মেইল পাওয়া যায়নি।")
            return

        latest_id = mail_ids[-1]
        status, msg_data = mail.fetch(latest_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # ইমেইল সাবজেক্ট ডিকোড করা
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                # বডি থেকে টেক্সট বের করা
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                # OTP এবং লিঙ্ক ফিল্টার করা
                otps, links = get_otp_and_links(body)

                response = f"📧 **Subject:** {subject}\n"
                response += "--------------------------\n"
                
                if otps:
                    response += f"🔢 **OTP Found:** `{otps[0]}`\n" # প্রথম যে কোডটি পাবে
                
                if links:
                    # প্রথম ২-৩টি লিঙ্ক হাইলাইট করা (ভেরিফাই লিঙ্কের জন্য)
                    response += f"\n🔗 **Verification Links:**\n"
                    for link in links[:2]: 
                        response += f"{link}\n"
                
                if not otps and not links:
                    response += "⚠️ কোনো কোড বা লিঙ্ক পাওয়া যায়নি, কিন্তু মেইল এসেছে।"

                bot.send_message(message.chat.id, response, disable_web_page_preview=True, parse_mode="Markdown")
        
        mail.logout()

    except Exception as e:
        bot.send_message(message.chat.id, "❌ লগইন ফেইল! ইমেইল/পাসওয়ার্ড চেক করুন অথবা IMAP অন আছে কি না দেখুন।")

bot.polling()
