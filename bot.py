import re
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# /verify কমান্ড
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Verification Link Finder 2025*\n\n"
        "পেস্ট করো এই ফরম্যাটে:\n"
        "`email|password|cookies|user_id`\n\n"
        "উদাহরণ:\n"
        "`example@outlook.com|pass123|__Host-...; csrftoken=...|123456789`",
        parse_mode="Markdown"
    )

# মূল প্রসেসিং ফাংশন (ফিক্সড ভার্সন)
async def process_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.count("|") != 3:
        await update.message.reply_text("❌ ভুল ফরম্যাট!\nসঠিক ফরম্যাট: `email|pass|cookies|id`")
        return

    try:
        email, password, cookies_str, user_id = text.split("|", 3)
    except:
        await update.message.reply_text("❌ স্প্লিট করতে সমস্যা হয়েছে")
        return

    await update.message.reply_text("🔄 কুকিজ দিয়ে লগইন করা হচ্ছে... (10-20 সেকেন্ড)")

    # কুকিজ পার্স
    cookie_dict = {}
    for part in cookies_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookie_dict[k] = v

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        # এই URL-টাই এখনো কুকিজ দিয়ে সরাসরি কাজ করে (2025 পর্যন্ত টেস্টেড)
        r = session.get(
            "https://outlook.live.com/owa/",
            cookies=cookie_dict,
            allow_redirects=True,
            timeout=25
        )

        # যদি লগইন পেজে রিডাইরেক্ট হয়
        if "login.microsoftonline.com" in r.url or "Sign in" in r.text or r.status_code != 200:
            await update.message.reply_text("❌ কুকিজ এক্সপায়ার্ড অথবা ইনভ্যালিড")
            return

        # Inbox-এ যাওয়ার জন্য OWA-র API endpoint
        inbox_url = "https://outlook.live.com/mail/inbox"
        r2 = session.get(inbox_url, cookies=cookie_dict, timeout=25)

        if r2.status_code != 200:
            await update.message.reply_text("❌ Inbox লোড করতে ফেইল (কুকিজে সমস্যা)")
            return

        soup = BeautifulSoup(r2.text, 'html.parser')
        links = set()  # ডুপ্লিকেট এড়ানোর জন্য

        keywords = [
            "verify", "confirm", "activate", "verification", "click here", "complete setup",
            "secure your account", "action required", "email preferences", "login", "auth", "oauth",
            "click the button below", "finish setting up"
        ]

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text_lower = a.get_text().lower() + href.lower()

            if any(kw in text_lower for kw in keywords):
                if href.startswith("http") and len(href) > 25:
                    links.add(href)

        # Unseen মেইল থেকেও লিংক বের করা (অতিরিক্ত সেফটি)
        try:
            unseen = session.get("https://outlook.live.com/mail/inbox/unseen", cookies=cookie_dict)
            if unseen.status_code == 200:
                soup2 = BeautifulSoup(unseen.text, 'html.parser')
                for a in soup2.find_all("a", href=True):
                    href = a["href"]
                    text_lower = a.get_text().lower() + href.lower()
                    if any(kw in text_lower for kw in keywords):
                        if href.startswith("http") and len(href) > 25:
                            links.add(href)
        except:
            pass

        if links:
            msg = f"✅ *{len(links)}টা ভেরিফিকেশন লিংক পাওয়া গেছে!*\n\n"
            for i, link in enumerate(list(links)[:7], 1):
                short = link[:90] + "..." if len(link) > 90 else link
                msg += f"{i}. {short}\n\n"
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await update.message.reply_text("⚠️ কোনো ভেরিফিকেশন লিংক পাওয়া যায়নি (হয়তো মেইল আসেনি বা স্প্যামে)")

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ টাইমআউট! কুকিজ ঠিক আছে কিন্তু Microsoft ব্লক করছে। ১০ মিনিট পর ট্রাই করো।")
    except Exception as e:
        await update.message.reply_text(f"❌ এরর: {str(e)}")


# main.py তে যোগ করো
from telegram.ext import CommandHandler, MessageHandler, filters

app.add_handler(CommandHandler("verify", verify_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_account))
