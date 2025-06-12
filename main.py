import requests, re, base64, random, string, time,httpx,uuid, asyncio,json,telebot
from telebot import types
from datetime import datetime, timedelta
from collections import deque
from threading import Thread
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
# from keep_alive import keep_alive
from faker import Faker
from b3api import Landleleo
fake = Faker()
import names
# keep_alive()


BOT_API_KEY = '7872507180:AAETKEbeNF_y5P-gCPE9BcG1vI12jhtVoq4'
OWNER_ID = 5958698769


bot = telebot.TeleBot(BOT_API_KEY)
AUTHORIZED_USER_IDS = [OWNER_ID]  


user_tasks = {}

# Load premium users from file
def load_premium_users():
    premium_users = {}
    try:
        with open('premium_users.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                user_id, expiry_date = line.strip().split(',')
                premium_users[int(user_id)] = datetime.strptime(expiry_date, '%Y-%m-%d')
    except FileNotFoundError:
        pass
    return premium_users

# Save premium users to file
def save_premium_users(premium_users):
    with open('premium_users.txt', 'w') as file:
        for user_id, expiry_date in premium_users.items():
            file.write(f'{user_id},{expiry_date.strftime("%Y-%m-%d")}\n')

premium_users = load_premium_users()
PREMIUM_GROUP_ID = "-1002676791492"

async def find_between(data, first, last):
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None

async def create_cvv_charge(fullz, session):
    try:
        print(fullz)
        cc, mes, ano, cvv = fullz.split("|")
        bin_info = await get_bin_info(cc[:6])
        email = ''.join(random.choices(string.ascii_letters, k=24)) + "@gmail.com"
        user_agent = UserAgent().random
        name = names.get_first_name()
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        postal_code = fake.zipcode()
        phone = f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
        # await asyncio.sleep(4)
        respone = Landleleo(cc, mes, ano, cvv)
        result = respone.chk()

        if result.get("CODE") == "AUTH_APPROVE":
            print(f"Approved {fullz}")
            return "Approved"

        elif result.get("CODE") == "AUTH_DECLINE":
            reason = result.get("Message", "Card Declined")
            return f"Declined: {reason}"

        else:
            print(f"Unknown response for {fullz}")
            return f"Declined: {result.get('Message', 'Unknown reason')}"
                            

    except Exception as e:
        return f"Error: {str(e)}"  # instead of return None or nothing


async def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}")
        data = response.json()
        bin_info = (
    f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {data.get('country_name', 'N/A')} {data.get('country_flag', 'N/A')}\n"
    
)


        return bin_info
    except Exception as e:
        return str(e)

async def multi_checking(x, chat_id, message_id):
    try:
        start = time.time()
        getproxy = random.choice(open("proxy.txt", "r", encoding="utf-8").read().splitlines())
        proxy_ip, proxy_port, proxy_user, proxy_password = getproxy.split(":")
        proxies = {
            "https://": f"http://{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}",
            "http://": f"http://{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}",
        }

        with httpx.Client(proxies=proxies, timeout=40) as session:
            result = await asyncio.to_thread(create_cvv_charge, x, session)


        end = time.time()
        resp = f"{x} - {result} - Taken {round(end - start, 2)}s"

        if chat_id and message_id:
            bot.edit_message_text(resp, chat_id, message_id)

        return result  # ✅ IMPORTANT LINE

    except Exception as e:
        print(f"Error in multi_checking: {str(e)}")
        return f"Error: {str(e)}"


def create_inline_keyboard(approved, declined, total, current_cc, total_ccs):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(f"Approved ✅ : {approved}", callback_data="approved"),
    )
    keyboard.row(
        types.InlineKeyboardButton(f"Declined ❌ : {declined}", callback_data="declined"),
    )
    keyboard.row(
        types.InlineKeyboardButton(f"Total 🚫 : {total}", callback_data="total"),
    )
    keyboard.row(
        types.InlineKeyboardButton(f"Total CCs in File 🚫 : {total_ccs}", callback_data="total_ccs"),
    )
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        welcome_message = """
👋 **Welcome to CC Checker Bot!** 👋

📜 **How to Use:**
1. **Send `/check <combo>`** - Start checking a CC combo.
2. **Upload a .txt file** - Upload a text file with CC combos to start checking.
3. **/cmd or /cmds** - More Commands Info

💡 *Note:* Only authorized users can access the bot. Contact @zi0xe for authorization.

🔒 **Stay secure and happy checking!** 🔒
        """
        bot.reply_to(message, welcome_message, parse_mode="Markdown")
    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact @zi0xe for authorization.
        """
        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")
@bot.message_handler(commands=['cmd', 'cmds'])
def send_commands(message):
    commands_text = """
📋*Command List for CC Checker Bot*📋

🔹 */start* or */help* - Get a welcome message and help info.
🔹 */check <combo>* - Start checking a CC combo.
🔹 */stop* - Stop the current checking process.
🔹 */pause* - Pause the current checking process.
🔹 */resume* - Resume the paused checking process.
🔹 *Upload a .txt file* - Upload a text file with CC combos to start checking.

💡 *Note:* Only authorized users can access the bot. Contact @zi0xe for authorization.
    """
    
    bot.send_message(message.chat.id, commands_text, parse_mode="Markdown")


@bot.message_handler(commands=['check'])
def check_cc(message):
    Thread(target=asyncio.run, args=(_check_cc(message),)).start()

async def _check_cc(message):
    global user_tasks
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]['is_running']:
            check_running_message = """
            ⏳ **Check in Progress** ⏳

            A check is already running. Please wait for it to finish or stop it using **/stop**.
            """

            bot.reply_to(message, check_running_message, parse_mode="Markdown")
            return
        try:
            combo = message.text.split('/check ')[1]
            ccs = combo.split('\n')
            user_tasks[message.from_user.id] = {
                'is_running': True,
                'is_paused': False,
                'queue': deque(ccs),
                'approved': [],
                'declined': [],
                'total': 0
            }
            start_check_message = """
            🔄 **Starting CC Check...** 🔄
            """

            msg = bot.reply_to(message, start_check_message, parse_mode="Markdown")


            total_ccs = len(ccs)
            while user_tasks[message.from_user.id]['queue']:
                while user_tasks[message.from_user.id]['is_paused']:
                    await asyncio.sleep(1)
                if not user_tasks[message.from_user.id]['is_running']:
                    break
                current_cc = user_tasks[message.from_user.id]['queue'].popleft()
                user_tasks[message.from_user.id]['total'] += 1
                keyboard = create_inline_keyboard(
                    len(user_tasks[message.from_user.id]['approved']),
                    len(user_tasks[message.from_user.id]['declined']),
                    user_tasks[message.from_user.id]['total'],
                    current_cc,
                    total_ccs
                )
                edit_check_message = f"""
🔍 **Checking:** `{current_cc}`
🚪 **Gate:** **Braintree Auth**
👨‍💻 **Developer:** **@zi0xe**
                """

                bot.edit_message_text(edit_check_message, message.chat.id, msg.message_id, reply_markup=keyboard, parse_mode="Markdown")

                result = await multi_checking(current_cc, message.chat.id, msg.message_id)
                if result and 'Approved' in result:

                    user_tasks[message.from_user.id]['approved'].append(current_cc)
                    bot.send_message(
    message.chat.id, 
    f"""
💳 **𝗖𝗖:** `{current_cc}`
🛠 **𝗚𝗮𝘁𝗲:** **Braintree Auth**
📝 **𝗗𝗲𝘁𝗮𝗶𝗹𝘀:** {result} ✅
👨‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** @zi0xe
    """,
    parse_mode="Markdown"
)

#                     bot.send_message(
#     PREMIUM_GROUP_ID, 
#     f"""
# 💳 **𝗖𝗖:** `{current_cc}`
# 🛠 **𝗚𝗮𝘁𝗲:** **Braintree Auth**
# 📝 **𝗗𝗲𝘁𝗮𝗶𝗹𝘀:** {result}
# 👨‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** @zi0xe
#     """,
#     parse_mode="Markdown"
# )

                else:
                    user_tasks[message.from_user.id]['declined'].append(current_cc)
                status_msg = f"Total: {user_tasks[message.from_user.id]['total']}\nApproved: {len(user_tasks[message.from_user.id]['approved'])}\nDeclined: {len(user_tasks[message.from_user.id]['declined'])}"
                bot.edit_message_text(status_msg, message.chat.id, msg.message_id, reply_markup=keyboard)
            check_completed_message = f"""
            ✅ **Check Completed!** ✅
            {user_tasks[message.from_user.id]['approved']}
            """

            bot.reply_to(message, check_completed_message, parse_mode="Markdown")

        except Exception as e:
            bot.reply_to(message, f"Error: {str(e)}")
        finally:
            user_tasks[message.from_user.id]['is_running'] = False
    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_checking(message):
    global user_tasks
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]['is_running']:
            user_tasks[message.from_user.id]['is_running'] = False
            stop_check_message = """
            🛑 **Stopping the Current Checking Process** 🛑
            """

            bot.reply_to(message, stop_check_message, parse_mode="Markdown")

        else:
            no_check_process_message = """
            🚫 **No Checking Process Running** 🚫
            """

            bot.reply_to(message, no_check_process_message, parse_mode="Markdown")

    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")

@bot.message_handler(commands=['pause'])
def pause_checking(message):
    global user_tasks
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]['is_running']:
            user_tasks[message.from_user.id]['is_paused'] = True
            pause_check_message = """
            ⏸️ **Pausing the Current Checking Process** ⏸️
            """

            bot.reply_to(message, pause_check_message, parse_mode="Markdown")

        else:
            no_checking_process_message = """
            🚫 **No Checking Process Running** 🚫
            """

            bot.reply_to(message, no_checking_process_message, parse_mode="Markdown")

    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")

@bot.message_handler(commands=['resume'])
def resume_checking(message):
    global user_tasks
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]['is_running']:
            user_tasks[message.from_user.id]['is_paused'] = False
            resume_check_message = """
            ▶️ **Resuming the Current Checking Process** ▶️
            """

            bot.reply_to(message, resume_check_message, parse_mode="Markdown")

        else:
            no_checking_process_message = """
            🚫 **No Checking Process Running** 🚫
            """

            bot.reply_to(message, no_checking_process_message, parse_mode="Markdown")

    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")

@bot.message_handler(commands=['premium'])
def add_premium_user(message):
    if message.from_user.id == OWNER_ID:
        try:
            _, user_id, days = message.text.split()
            user_id = int(user_id)
            days = int(days)
            expiry_date = datetime.now() + timedelta(days=days)
            premium_users[user_id] = expiry_date
            save_premium_users(premium_users)
            premium_user_added_message = f"""
            🌟 **Premium User Added** 🌟

            User **{user_id}** has been added as a premium user for **{days} days**.
            """

            bot.reply_to(message, premium_user_added_message, parse_mode="Markdown")

            premium_access_message = f"""
            🌟 **Premium Access Granted** 🌟

            You have been granted premium access for **{days} days**.
            """

            bot.send_message(user_id, premium_access_message, parse_mode="Markdown")

        except Exception as e:
            bot.reply_to(message, f"Error: {str(e)}")
    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    Thread(target=asyncio.run, args=(_handle_docs(message),)).start()

async def _handle_docs(message):
    global user_tasks
    if message.from_user.id in AUTHORIZED_USER_IDS or message.from_user.id in premium_users:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]['is_running']:
            check_running_message = """
            ⏳ **Check Already Running** ⏳

            A check is already running. Please wait for it to finish or stop it using **/stop**.
            """

            bot.reply_to(message, check_running_message, parse_mode="Markdown")

            return
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(f"{message.document.file_name}", 'wb') as new_file:
                new_file.write(downloaded_file)

            with open(f"{message.document.file_name}", 'r', encoding='utf-8') as file:
                ccs = file.read().splitlines()

            user_tasks[message.from_user.id] = {
                'is_running': True,
                'is_paused': False,
                'queue': deque(ccs),
                'approved': [],
                'declined': [],
                'total': 0
            }
            start_check_message = """
            🔄 **Starting CC Check...** 🔄
            """

            msg = bot.reply_to(message, start_check_message, parse_mode="Markdown")

            total_ccs = len(ccs)
            while user_tasks[message.from_user.id]['queue']:
                while user_tasks[message.from_user.id]['is_paused']:
                    await asyncio.sleep(1)
                if not user_tasks[message.from_user.id]['is_running']:
                    break
                current_cc = user_tasks[message.from_user.id]['queue'].popleft()
                user_tasks[message.from_user.id]['total'] += 1
                keyboard = create_inline_keyboard(
                    len(user_tasks[message.from_user.id]['approved']),
                    len(user_tasks[message.from_user.id]['declined']),
                    user_tasks[message.from_user.id]['total'],
                    current_cc,
                    total_ccs
                )
                edit_check_message = f"""
🔍 **Checking:** `{current_cc}`
🚪 **Gate:** **Braintree Auth**
👨‍💻 **Developer:** **@zi0xe**
                """

                bot.edit_message_text(edit_check_message, message.chat.id, msg.message_id, reply_markup=keyboard, parse_mode="Markdown")

                result = await multi_checking(current_cc, message.chat.id, msg.message_id)
                if result and 'Approved' in result:
                    user_tasks[message.from_user.id]['approved'].append(current_cc)
                    bot.send_message(
    message.chat.id, 
    f"""
💳 **𝗖𝗖:** `{current_cc}`
🛠 **𝗚𝗮𝘁𝗲:** **Braintree Auth**
📝 **𝗗𝗲𝘁𝗮𝗶𝗹𝘀:** {result} ✅
👨‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** @zi0xe
    """,
    parse_mode="Markdown"
)

#                     bot.send_message(
#     PREMIUM_GROUP_ID, 
#     f"""
# 💳 **𝗖𝗖:** `{current_cc}`
# 🛠 **𝗚𝗮𝘁𝗲:** **Braintree Auth**
# 📝 **𝗗𝗲𝘁𝗮𝗶𝗹𝘀:** {result}
# 👨‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** @zi0xe
#     """,
#     parse_mode="Markdown"
# )

                else:
                    user_tasks[message.from_user.id]['declined'].append(current_cc)
                status_msg = f"Approved: {len(user_tasks[message.from_user.id]['approved'])}\nDeclined: {len(user_tasks[message.from_user.id]['declined'])}\nTotal: {user_tasks[message.from_user.id]['total']}"
                bot.edit_message_text(status_msg, message.chat.id, msg.message_id, reply_markup=keyboard)
            check_completed_message = f"""
            ✅ **Check Completed!** ✅

            **Approved:**
            {user_tasks[message.from_user.id]['approved']}
            """

            bot.reply_to(message, check_completed_message, parse_mode="Markdown")


        except Exception as e:
            bot.reply_to(message, f"Error: {str(e)}")
        finally:
            user_tasks[message.from_user.id]['is_running'] = False
    else:
        unauthorized_message = """
🚫 **Access Denied** 🚫

You are not authorized to use this bot. Please contact **@zi0xe** for authorization.
"""

        bot.reply_to(message, unauthorized_message, parse_mode="Markdown")


bot.infinity_polling()
