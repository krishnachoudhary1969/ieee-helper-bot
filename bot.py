import os
import sqlite3
import time as t
from collections import defaultdict
from openpyxl import Workbook

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# ================= CONFIG =================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = -1003523110008
ADMIN_IDS = {2087320275}
LINKTREE = "https://linktr.ee/IEEE_SB_GEHU"

# ============ FEATURE FLAGS ==============
RSVP_ACTIVE = False
ATTENDANCE_ACTIVE = False
FEEDBACK_ACTIVE = False

RSVP_LINK = ""
FEEDBACK_LINK = ""
# =========================================

last_msg = defaultdict(float)

# ================= DB ====================
conn = sqlite3.connect("ieee_logs.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    user_id INTEGER,
    name TEXT,
    timestamp TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS joins(
    user_id INTEGER,
    name TEXT,
    timestamp TEXT
)
""")
conn.commit()
# =========================================


# ================= UTIL ==================
def is_admin(update):
    return update.effective_user.id in ADMIN_IDS


async def delete_cmd(update):
    if update.message:
        try:
            await update.message.delete()
        except:
            pass
# =========================================


# ================= JOIN ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:

        # log join
        cur.execute(
            "INSERT INTO joins VALUES (?, ?, datetime('now'))",
            (member.id, member.first_name)
        )
        conn.commit()

        # DM linktree
        try:
            await context.bot.send_message(
                chat_id=member.id,
                text=(
                    "👋 Welcome to IEEE SB GEHU!\n\n"
                    "Start the bot to access resources:\n"
                    f"{LINKTREE}"
                )
            )
        except:
            pass
# =========================================


# ================= HELP ==================
async def help_cmd(update, context):
    if is_admin(update):
        text = (
            "Admin Commands:\n"
            "/rsvp_on\n/attendance_on\n/export\n/stats\n"
            "/certificate\n/remind\n/feedback_on"
        )
    else:
        text = (
            "User Commands:\n"
            "/rules\n/events"
        )

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text
    )
# =========================================


# ================= RSVP ==================
async def rsvp_on(update, context):
    global RSVP_ACTIVE, RSVP_LINK
    await delete_cmd(update)

    if not is_admin(update):
        return

    RSVP_ACTIVE = True
    RSVP_LINK = context.args[-1]
    event_name = " ".join(context.args[:-1])

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Register Now", url=RSVP_LINK)]]
    )

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"🎉 *{event_name}*\nRegister below 👇",
        parse_mode="Markdown",
        reply_markup=button
    )


async def rsvp_off(update, context):
    global RSVP_ACTIVE
    await delete_cmd(update)
    RSVP_ACTIVE = False
# =========================================


# ================= FEEDBACK ==============
async def feedback_on(update, context):
    global FEEDBACK_ACTIVE, FEEDBACK_LINK
    await delete_cmd(update)

    if not is_admin(update):
        return

    FEEDBACK_ACTIVE = True
    FEEDBACK_LINK = context.args[0]

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📝 Submit Feedback", url=FEEDBACK_LINK)]]
    )

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text="We value your feedback 👇",
        reply_markup=button
    )


async def feedback_off(update, context):
    global FEEDBACK_ACTIVE
    await delete_cmd(update)
    FEEDBACK_ACTIVE = False
# =========================================


# ================= ATTENDANCE ============
async def attendance_on(update, context):
    global ATTENDANCE_ACTIVE
    await delete_cmd(update)

    if is_admin(update):
        ATTENDANCE_ACTIVE = True


async def attendance_off(update, context):
    global ATTENDANCE_ACTIVE
    await delete_cmd(update)

    if is_admin(update):
        ATTENDANCE_ACTIVE = False
# =========================================


# ================= ANTI-SPAM + ATTENDANCE
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    uid = update.effective_user.id
    now = t.time()

    # link block
    if "http://" in update.message.text or "https://" in update.message.text:
        await update.message.delete()
        return

    # rate limit
    if now - last_msg[uid] < 2:
        await update.message.delete()
        return

    last_msg[uid] = now

    # attendance logging
    if ATTENDANCE_ACTIVE:
        cur.execute(
            "INSERT INTO attendance VALUES (?, ?, datetime('now'))",
            (uid, update.effective_user.first_name)
        )
        conn.commit()
# =========================================


# =========================================
async def export_attendance(update, context):
    if not is_admin(update):
        return

    wb = Workbook()
    ws = wb.active
    ws.append(["User ID", "Name", "Timestamp"])

    rows = cur.execute("SELECT * FROM attendance").fetchall()

    for r in rows:
        ws.append(r)

    file_name = "attendance.xlsx"
    wb.save(file_name)

    await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=open(file_name, "rb")
    )
# =========================================


# =========================================
async def stats(update, context):
    if not is_admin(update):
        return

    total = cur.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    joins = cur.execute("SELECT COUNT(*) FROM joins").fetchone()[0]

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"📊 Dashboard\n\nJoins: {joins}\nAttendance: {total}"
    )
# =========================================


# =========================================
async def certificate(update, context):
    if not is_admin(update):
        return

    name = " ".join(context.args)
    if not name:
        return

    file = f"{name}_certificate.txt"

    with open(file, "w") as f:
        f.write(
            f"Certificate of Participation\n\n"
            f"This certifies that {name}\n"
            f"participated in IEEE SB GEHU Event."
        )

    await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=open(file, "rb")
    )
# =========================================


# =========================================
async def remind(update, context):
    if not is_admin(update):
        return

    delay = int(context.args[0])  # seconds
    msg = " ".join(context.args[1:])

    context.job_queue.run_once(
        lambda ctx: ctx.bot.send_message(chat_id=CHANNEL_ID, text=msg),
        delay
    )
# =========================================


# ================= MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("help", help_cmd))

    # admin toggles
    app.add_handler(CommandHandler("rsvp_on", rsvp_on))
    app.add_handler(CommandHandler("rsvp_off", rsvp_off))
    app.add_handler(CommandHandler("feedback_on", feedback_on))
    app.add_handler(CommandHandler("feedback_off", feedback_off))
    app.add_handler(CommandHandler("attendance_on", attendance_on))
    app.add_handler(CommandHandler("attendance_off", attendance_off))
    app.add_handler(CommandHandler("export", export_attendance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("certificate", certificate))
    app.add_handler(CommandHandler("remind", remind))



    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    
    app.run_polling(
    drop_pending_updates=True,
    close_loop=False
    )


if __name__ == "__main__":
    main()
