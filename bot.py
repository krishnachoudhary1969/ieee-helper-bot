import os
from datetime import time
from collections import defaultdict
import time as t

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# ---------- CONFIG ----------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = -1003523110008
ADMIN_IDS = {2087320275}
# ----------------------------

last_msg = defaultdict(float)

# ---------- COMMANDS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to IEEE Student Branch – GEHU 👋\n"
        "Type /help to see available commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Introduction\n"
        "/help - Commands\n"
        "/rules - Community rules\n"
        "/events - Upcoming events\n"
        "/announce - Admin announcement\n"
        "/poll - Create a poll"
    )

# cooldown storage
rules_cooldown = {}

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = (
        "📜 *IEEE SB GEHU Rules*\n"
        "1. Be respectful\n"
        "2. No spam\n"
        "3. IEEE-related discussions only"
    )

    user_id = update.effective_user.id
    now = t.time()
    # 30 sec cooldown per user
    if user_id in rules_cooldown and now - rules_cooldown[user_id] < 30:
        return
    rules_cooldown[user_id] = now

    # If command used in group → DM user instead
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=rules_text,
                parse_mode="Markdown"
            )
            await update.message.reply_text(
                "📩 Rules sent to your DM!"
            )
        except:
            pass
    else:
        # Private chat
        await update.message.reply_text(
            rules_text,
            parse_mode="Markdown"
        )


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Upcoming IEEE Events:\n"
        "• SAARTHI'25 Hackathon – Dates TBA\n"
        "• Technical Workshop – Coming Soon"
    )

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /announce <message>")
        return

    await context.bot.send_message(chat_id=CHANNEL_ID, text=text)

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="Will you participate?",
        options=["Yes", "Maybe", "No"],
        is_anonymous=False
    )

# ---------- GROUP ----------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"Welcome {member.first_name} 👋\nPlease read /rules."
        )

async def anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore updates without a user or text (channels, system messages, etc.)
    if not update.effective_user or not update.message or not update.message.text:
        return

    uid = update.effective_user.id
    now = t.time()

    # Delete links
    if "http://" in update.message.text or "https://" in update.message.text:
        await update.message.delete()
        return

    # Rate limiting
    if now - last_msg[uid] < 2:
        await update.message.delete()
        return

    last_msg[uid] = now


async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin check
    if update.effective_user.id not in ADMIN_IDS:
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "Usage: /reminder <message>"
        )
        return

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📢 *IEEE Reminder*\n{text}",
        parse_mode="Markdown"
    )


# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("poll", poll))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam))

    app.add_handler(CommandHandler("reminder", reminder))


    app.run_polling()

if __name__ == "__main__":
    main()
