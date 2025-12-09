# ====== নতুন ফিচার: তোমার ফরম্যাটে (email|pass|cookies|id) পেস্ট করলে লিংক দেখাবে ======
import re
import requests
from bs4 import BeautifulSoup

# /verify কমান্ড
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Verification Link Finder*\n\n"
        "Paste account in this format:\n"
        "`email|password|cookies|id`\n\n"
        "Example:\n"
        "`daniel@outlook.com|pass123|__Host-M...|user_id`",
        parse_mode="Markdown"
    )

# কুকিজ পার্স করে লগইন
async def process_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "|" not in text or text.count("|") != 3:
        await update.message.reply_text("Wrong format! Use: email|pass|cookies|id")
        return
    
    email, password, cookies_str, user_id = text.split("|", 3)
    
    await update.message.reply_text("Logging in with cookies... 10-15 sec")
    
    try:
        # কুকিজকে ডিকশনারিতে কনভার্ট
        cookie_dict = {}
        for part in cookies_str.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookie_dict[k] = v
        
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Outlook ইনবক্সে যাওয়া
        r = session.get("https://outlook.live.com/mail/inbox", cookies=cookie_dict, headers=headers, timeout=20)
        
        if "Sign in" in r.text or r.status_code != 200:
            await update.message.reply_text("Failed — Cookies expired or invalid")
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')
        links = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(kw in href.lower() for kw in ["verify", "confirm", "activate", "click here", "complete", "login", "auth", "oauth"]):
                if href.startswith("http") and len(href) > 30:
                    links.append(href)
        
        if links:
            msg = "*Verification Links Found!*\n\n"
            for i, link in enumerate(links[:5], 1):
                short = link[:80] + "..." if len(link) > 80 else link
                msg += f"{i}. {short}\n\n"
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await update.message.reply_text("No verification link found in inbox")
            
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# main() এ যোগ করো
app.add_handler(CommandHandler("verify", verify_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_account))  # যেকোনো টেক্সট পেলে চেক করবে
