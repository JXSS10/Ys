# helpers.py

import time
from datetime import timedelta
import re
import os
import asyncio
import logging
import pyrogram
from config import ADMIN_IDS, FORCE_SUBSCRIBE_CHANNEL_ID, DEFAULT_THUMBNAIL
from database import digital_botz
from language_handler import get_text

logger = logging.getLogger(__name__)

async def is_pro_user(user_id):
    """Check if user is a pro user based on database."""
    return await digital_botz.has_premium_access(user_id) # Corrected function name to match database.py

def is_admin(user_id):
    """Check if user is an admin."""
    return user_id in ADMIN_IDS

async def is_admin_or_pro(user_id):
    """Check if user is admin or pro user."""
    return is_admin(user_id) or await is_pro_user(user_id)

def get_uptime(bot_start_time): # استقبل bot_start_time كمعامل
    """Calculate bot uptime."""
    current_time = time.time()
    uptime_seconds = current_time - bot_start_time
    uptime = timedelta(seconds=int(uptime_seconds))
    return str(uptime)

def get_speed_and_eta(start_time, current, total):
    """Calculate download/upload speed and ETA."""
    if current == 0:
        return "N/A", "N/A"
    elapsed_time = time.time() - start_time
    speed_bytes = current / elapsed_time
    speed = get_readable_size(speed_bytes) + '/s'
    if current == total:
        eta = "Completed"
    else:
        remaining_bytes = total - current
        if speed_bytes > 0:
            eta_seconds = remaining_bytes / speed_bytes
            eta = timedelta(seconds=int(eta_seconds))
        else:
            eta = "N/A"
    return speed, str(eta)

last_edit_time = 0  # Initialize last_edit_time globally

async def progress(current, total, message, type, start_time, initial_message, bot): # استقبل bot كمعامل
    global last_edit_time
    lang = await get_user_language(message.from_user.id)
    percentage = current * 100 / total
    completed_bar = int(20 * current // total)
    remaining_bar = 20 - completed_bar
    progress_bar = '▣' * completed_bar + '▢' * remaining_bar
    speed, eta = get_speed_and_eta(start_time, current, total)

    progress_message_text = f"""

{type.upper()} STARTED....

{progress_bar}

╭━━━━❰@x_xf8 PROCESSING...❱━➣
┣⪼ 🗂️ ꜱɪᴢᴇ: {get_readable_size(current)} | {get_readable_size(total)}
┣⪼ ⏳️ ᴅᴏɴᴇ : {percentage:.2f}%
┣⪼ 🚀 ꜱᴩᴇᴇᴅ: {speed}
┣⪼ ⏰️ ᴇᴛᴀ: {eta}
╰━━━━━━━━━━━━━━━➣
"""
    current_time = time.time()
    if current_time - last_edit_time >= 4:
        try:
            await bot.edit_message_text(message.chat.id, initial_message.id, progress_message_text) # استخدم bot المستلم كمعامل
            logger.info(f"Progress updated in message: {message.id}, Progress: {type}, Percentage: {percentage:.2f}%")
            last_edit_time = current_time
        except FloodWait as e:
            logger.warning(f"FloodWait encountered during progress update (EditMessage), waiting for {e.value} seconds.")
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.error(f"Error updating progress message: {e}")
    else:
        logger.debug("Skipping progress update due to time throttling (4 seconds).")
    logger.info(f"Progress (log only): {type}, Current: {current}, Total: {total}, Percentage: {percentage:.2f}%")

def get_readable_size(size_bytes):
    if size_bytes >= (1024**3):
        size = size_bytes / (1024**3)
        suffix = 'GB'
    elif size_bytes >= (1024**2):
        size = size_bytes / (1024**2)
        suffix = 'MB'
    elif size_bytes >= 1024:
        size = size_bytes / 1024
        suffix = 'KB'
    else:
        size = size_bytes
        suffix = 'Bytes'
    return f"{size:.2f} {suffix}"

def clean_filename(text):
    text = re.sub(r'[/:*?"<>|]', "", text)
    text = text.replace(" ", "_")
    return text

async def forward_message_to_log_channel(message, bot, file=False): # استقبل bot كمعامل
    try:
        if file:
            await bot.copy_message( # استخدم bot المستلم كمعامل
                chat_id=LOG_CHANNEL_ID,
                from_chat_id=message.chat.id,
                message_id=message.id
            )
        else:
            await bot.forward_messages( # استخدم bot المستلم كمعامل
                chat_id=LOG_CHANNEL_ID,
                from_chat_id=message.chat.id,
                message_ids=message.id
            )
        logger.info(f"Message forwarded to log channel from chat ID: {message.chat.id}, message ID: {message.id}")
    except Exception as e:
        logger.error(f"Error forwarding message to log channel: {e}")

async def send_user_info_to_log_channel(user, lang, bot): # استقبل bot كمعامل
    try:
        user_info = get_text("user_info_message", lang,
                                user_first_name=user.first_name,
                                user_last_name=user.last_name if user.last_name else '',
                                user_username=f"@{user.username}" if user.username else "None",
                                user_id=user.id,
                                entry_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        chat = await bot.get_chat(user.id) # استخدم bot المستلم كمعامل
        if chat.photo:
            profile_photo = await bot.download_media(chat.photo.big_file_id) # استخدم bot المستلم كمعامل
            await bot.send_photo(LOG_CHANNEL_ID, profile_photo, caption=user_info) # استخدم bot المستلم كمعامل
            os.remove(profile_photo)
        else:
            await bot.send_message(LOG_CHANNEL_ID, user_info) # استخدم bot المستلم كمعامل

        logger.info(f"User {user.id} info sent to log channel.")

    except Exception as e:
        logger.error(f"Error sending user info to log channel: {e}")


def check_daily_task_limit(user_id, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # استقبل المتغيرات ذات الصلة بالحد كمعاملات
    current_day = datetime.now().day

    if last_task_reset_day != current_day:
        user_daily_tasks = {}
        last_task_reset_day = current_day
        logger.info("Daily task limit reset for all users.")

    if user_id not in user_daily_tasks:
        user_daily_tasks[user_id] = DAILY_TASK_LIMIT

    if user_daily_tasks[user_id] > 0:
        return True
    else:
        return False


def decrement_daily_task_count(user_id, user_daily_tasks): # استقبل user_daily_tasks كمعامل
    if user_id in user_daily_tasks:
        user_daily_tasks[user_id] -= 1
        logger.info(f"User {user_id} task count decremented. Remaining tasks: {user_daily_tasks[user_id]}")
    else:
        logger.warning(f"User {user_id} not found in daily task counts. This should not happen.")

async def is_user_subscribed(client, user_id): # تم تبسيط المعاملات
    try:
        member = await client.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id) # استخدم FORCE_SUBSCRIBE_CHANNEL_ID من config
        return member.status not in ("left", "banned")
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return False

async def force_subscribe(client, message, lang, bot): # استقبل bot كمعامل
    user_id = message.from_user.id
    if not await is_user_subscribed(client, user_id): # تم تبسيط الاستدعاء
        channel = await bot.get_chat(FORCE_SUBSCRIBE_CHANNEL_ID) # استخدم bot المستلم كمعامل و FORCE_SUBSCRIBE_CHANNEL_ID من config
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text("subscribe_button", lang), url=f"https://t.me/{channel.username}")]]
        )
        await message.reply_text(
            get_text("subscribe_message", lang),
            reply_markup=markup,
            quote=True
        )
        return False
    return True

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try: msg.document.file_id; return "Document"
    except: pass
    try: msg.video.file_id; return "Video"
    except: pass
    try: msg.animation.file_id; return "Animation"
    except: pass
    try: msg.sticker.file_id; return "Sticker"
    except: pass
    try: msg.voice.file_id; return "Voice"
    except: pass
    try: msg.audio.file_id; return "Audio"
    except: pass
    try: msg.photo.file_id; return "Photo"
    except: pass
    try: msg.text; return "Text"
    except: pass
    return "Unknown"
