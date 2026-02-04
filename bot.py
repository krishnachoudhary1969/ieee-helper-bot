import os
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

RULES_TEXT = (
    "📜 *IEEE SB GEHU Rules*\n"
    "1. Be respectful\n"
    "2. No spam\n"
    "3. IEEE-related discussions only"
)

HELP_TEXT = (
    "🤖 *IEEE Helper Commands*\n\n"
    "/rules – Community rules\n"
    "/events – Upcoming events\n"
    "/announce – Admin only\n"
    "/reminder – Admin only\n"
    "/poll – Create poll"
)

# ----------------------------

last_msg = defaultdict(float)
rules_cooldown = {}
pinned_rules = False


# =====================================================
# 🔹 UTILITY
# =====================================================

async def delete_command(update: Update):
    """Delete command message to keep group clean"""
    if update.message:
        try:
            await update.message.delete()
        except:
            pass


def is_admin(update: Update):
    return update.effective_user.id in ADMIN_IDS


# =====================================================
# 🔹 COMMANDS (DM only)
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi 👋 I'm IEEE Helper Bot.\nType /help")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    # Always DM help
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=HELP_TEXT,
        parse_mode="Markdown"
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    user_id = update.effective_user.id
    now = t.time()

    # cooldown
    if user_id in rules_cooldown and now - rules_cooldown[user_id] < 30:
        return
    rules_cooldown[user_id] = now

    await context.bot.send_message(
        chat_id=user_id,
        text=RULES_TEXT,
        parse_mode="Markdown"
    )


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="• SAARTHI'25 Hackathon – TBA\n• Workshop – Coming soon"
    )


# =====================================================
# 🔹 ADMIN COMMANDS
# =====================================================

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    if not is_admin(update):
        return

    text = " ".join(context.args)
    if not text:
        return

    await context.bot.send_message(chat_id=CHANNEL_ID, text=text)


async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    if not is_admin(update):
        return

    text = " ".join(context.args)
    if not text:
        return

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📢 *IEEE Reminder*\n{text}",
        parse_mode="Markdown"
    )


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_command(update)

    if not is_admin(update):
        return

    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="Will you participate?",
        options=["Yes", "Maybe", "No"],
        is_anonymous=False
    )


# =====================================================
# 🔹 GROUP FEATURES
# =====================================================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome + auto-pin rules once"""
    global pinned_rules

    for member in update.message.new_chat_members:
        msg = await update.message.reply_text(
            f"Welcome {member.first_name} 👋\nCheck your DM for rules."
        )

        # DM rules
        await context.bot.send_message(
            chat_id=member.id,
            text=RULES_TEXT,
            parse_mode="Markdown"
        )

        # Pin rules only once
        if not pinned_rules:
            rules_msg = await update.message.reply_text(RULES_TEXT, parse_mode="Markdown")
            await rules_msg.pin()
            pinned_rules = True


async def anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Link blocking + rate limit + topic moderation"""

    if not update.message or not update.message.text or not update.effective_user:
        return

    uid = update.effective_user.id
    now = t.time()

    text = update.message.text.lower()

    # delete links
    if "http://" in text or "https://" in text:
        await update.message.delete()
        return

    # rate limit
    if now - last_msg[uid] < 2:
        await update.message.delete()
        return

    last_msg[uid] = now

    # ---------- Topic moderation ----------
    # example: only admins allowed in "Announcements" topic
    if update.message.message_thread_id == 1 and not is_admin(update):
        await update.message.delete()


# =====================================================
# 🔹 MAIN
# =====================================================

def main():
    app = Application.builder().token(TOKEN).build()

    # user commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("events", events))

    # admin commands
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("reminder", reminder))
    app.add_handler(CommandHandler("poll", poll))

    # group
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam))

    app.run_polling()


if __name__ == "__main__":
    main()
