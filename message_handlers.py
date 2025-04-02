# message_handlers.py

import pyrogram
from pyrogram import filters
from pyrogram.errors import FloodWait, PeerIdInvalid, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import os
import asyncio
import urllib.parse
import re
from tqdm import tqdm
import logging

from config import DEFAULT_THUMBNAIL, DAILY_TASK_LIMIT
from helpers import is_admin_or_pro, check_daily_task_limit, decrement_daily_task_count, force_subscribe, get_readable_size, get_speed_and_eta, progress, clean_filename, forward_message_to_log_channel, get_message_type
from language_handler import get_text, get_user_language
from database import digital_botz

logger = logging.getLogger(__name__)

active_downloads = {}
active_uploads = {}
pending_link_choices = {}
current_task = None
thumb_state = {}

@pyrogram.Client.on_message(filters.text)
async def save_message_handler(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message, user_daily_tasks, last_task_reset_day): # تمرير المتغيرات ذات الصلة بالحد كمعاملات
    lang = await get_user_language(message.from_user.id)
    if not await force_subscribe(client, message, lang, client): # تمرير client إلى force_subscribe
        return

    user_id_check = message.from_user.id

    if not await is_admin_or_pro(user_id_check):
        if not check_daily_task_limit(user_id_check, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # تمرير المتغيرات ذات الصلة بالحد
            await message.reply_text(get_text("daily_limit_reached", lang, DAILY_TASK_LIMIT), reply_to_message_id=message.id)
            return

    user_id_log = message.from_user.id
    logger.info(f"Save function called. Message from user/chat ID: {user_id_log}, Text: {message.text}") # ADDED LOGGING

    if "https://t.me/" in message.text:
        logger.info("Link detected in message.") # ADDED LOGGING
        if "bulk" in message.text:
            await handle_bulk_link(message, client, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT) # تمرير client والمتغيرات ذات الصلة بالحد
        else:
            await handle_single_link(message, client, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT) # تمرير client والمتغيرات ذات الصلة بالحد
        return
    else:
        logger.info("No link detected in message.") # ADDED LOGGING

    if not await is_admin_or_pro(user_id_check):
        await message.reply_text(
            get_text("not_admin_message", lang),
            reply_to_message_id=message.id
        )

@pyrogram.Client.on_message(filters.photo)
async def handle_photo_messages_handler(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    lang = await get_user_language(message.from_user.id)
    if not await force_subscribe(client, message, lang, client): # تمرير client إلى force_subscribe
        return

    admin_user_id = message.from_user.id

    if thumb_state.get('thumb_target_user') and thumb_state.get('thumb_admin_user') == admin_user_id and helpers.is_admin(admin_user_id): # استخدام helpers.is_admin
        await set_user_thumbnail_from_admin_photo(client, message)

    elif helpers.is_admin(admin_user_id): # استخدام helpers.is_admin
        await auto_set_thumbnail_admin_photo(client, message)
    else:
        await forward_message_to_log_channel(message, client) # تمرير client إلى forward_message_to_log_channel

async def auto_set_thumbnail_admin_photo(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    lang = await get_user_language(message.from_user.id)
    admin_user_id = message.from_user.id

    if not helpers.is_admin(admin_user_id): # استخدام helpers.is_admin
        await message.reply_text(get_text("not_admin_command_message", lang), reply_to_message_id=message.id)
        return

    if thumb_state.get('thumb_target_user') is None or thumb_state.get('thumb_admin_user') != admin_user_id:
        thumb_file = await client.download_media(message.photo.file_id) # استخدام client المستلم كمعامل
        await digital_botz.set_thumbnail(admin_user_id, thumb_file)
        await message.reply_text(get_text("thumb_auto_set_admin", lang), reply_to_message_id=message.id)
    else:
        pass

async def set_user_thumbnail_from_admin_photo(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    lang = await get_user_language(message.from_user.id)
    admin_user_id = message.from_user.id
    target_user_id = thumb_state.get('thumb_target_user')
    thumb_admin_user = thumb_state.get('thumb_admin_user')

    if target_user_id and thumb_admin_user == admin_user_id and helpers.is_admin(admin_user_id): # استخدام helpers.is_admin
        try:
            target_user = await client.get_users(target_user_id) # استخدام client المستلم كمعامل
            if not target_user:
                await message.reply_text(get_text("user_not_found", lang, user_id=target_user_id), reply_to_message_id=message.id)
                return

            thumb_file = await client.download_media(message.photo.file_id) # استخدام client المستلم كمعامل
            await digital_botz.set_thumbnail(target_user_id, thumb_file)

            await message.reply_text(get_text("thumb_set_success_user", lang, user_id=target_user_id), reply_to_message_id=message.id)


        except Exception as e:
            await message.reply_text(get_text("error_setting_thumb", lang, error=e), reply_to_message_id=message.id)
        finally:
            thumb_state['thumb_target_user'] = None
            thumb_state['thumb_admin_user'] = None

async def handle_single_link(message: pyrogram.types.messages_and_media.message.Message, bot, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # استقبل bot والمتغيرات ذات الصلة بالحد كمعاملات
    lang = await get_user_language(message.from_user.id)
    if not await force_subscribe(bot, message, lang, bot): # تمرير bot إلى force_subscribe
        return

    user_id = message.from_user.id
    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
        if not check_daily_task_limit(user_id, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # تمرير المتغيرات ذات الصلة بالحد
            await message.reply_text(get_text("daily_limit_reached", lang, DAILY_TASK_LIMIT), reply_to_message_id=message.id)
            return

    global current_task
    current_task = message.text
    logger.info(f"handle_single_link called with link: {message.text}") # ADDED LOGGING

    try:
        parsed_url = urllib.parse.urlparse(message.text)
        logger.info(f"Parsed URL: {parsed_url}") # ADDED LOGGING
        path_segments = parsed_url.path.strip('/').split('/')
        logger.info(f"Path segments: {path_segments}") # ADDED LOGGING

        if parsed_url.netloc == 't.me' and len(path_segments) >= 2:
            if path_segments[0] == 'c': # Private channel/group link
                try:
                    chat_id = int("-100" + path_segments[1])
                    msg_id = int(path_segments[2])
                    logger.info(f"Private link - chat_id: {chat_id}, msg_id: {msg_id}") # ADDED LOGGING
                except ValueError as ve:
                    logger.error(f"ValueError parsing private link: {ve}") # ADDED LOGGING
                    await message.reply_text(get_text("error_generic", lang, error="Invalid link format (private channel)."), reply_to_message_id=message.id)
                    return
                await process_media_download_upload(message, chat_id, msg_id, lang, bot, user_daily_tasks) # تمرير bot و user_daily_tasks

            else: # Public channel/group link
                chat_username = path_segments[0]
                try:
                    msg_id = int(path_segments[1])
                    chat_entity = await bot.get_chat(chat_username) # استخدام bot المستلم كمعامل
                    chat_id = chat_entity.id
                    logger.info(f"Public link - chat_username: {chat_username}, msg_id: {msg_id}, chat_id: {chat_id}") # ADDED LOGGING
                except ValueError as ve:
                    logger.error(f"ValueError parsing public link (msg ID): {ve}") # ADDED LOGGING
                    await message.reply_text(get_text("error_generic", lang, error="Invalid link format (public channel - msg ID)."), reply_to_message_id=message.id)
                    return
                except PeerIdInvalid as pe:
                    logger.error(f"PeerIdInvalid for public link: {pe}") # ADDED LOGGING
                    await message.reply_text(get_text("error_generic", lang, error=f"Invalid public channel username: {chat_username}"), reply_to_message_id=message.id)
                    return

                # Offer choices for public links
                choice_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(get_text("choice_send_now", lang), callback_data=f"send_now_{chat_id}_{msg_id}"),
                        InlineKeyboardButton(get_text("choice_download_upload", lang), callback_data=f"download_upload_{chat_id}_{msg_id}")
                    ]
                ])
                choice_message = await message.reply_text(get_text("choice_public_link", lang), reply_markup=choice_markup, quote=True)
                pending_link_choices[message.id] = {"chat_id": chat_id, "msg_id": msg_id, "choice_message_id": choice_message.id, "user_id": user_id, "lang": lang}

                async def wait_for_choice():
                    await asyncio.sleep(3)
                    if message.id in pending_link_choices:
                        choice_data = pending_link_choices.pop(message.id)
                        try:
                            await bot.edit_message_text(message.chat.id, choice_data["choice_message_id"], get_text("choice_timeout", lang)) # استخدام bot المستلم كمعامل
                        except:
                            pass # Message might be deleted already
                        await process_media_send_now(message, choice_data["chat_id"], choice_data["msg_id"], choice_data["lang"], bot, user_daily_tasks) # تمرير bot و user_daily_tasks
                asyncio.create_task(wait_for_choice()) # Start timeout task
                return # Stop processing here, wait for callback

        else:
            await message.reply_text(get_text("error_generic", lang, error="Invalid Telegram link."), reply_to_message_id=message.id)
            return

    except Exception as e:
        logger.error(f"Error in handle_single_link (link parsing): {e}", exc_info=True) # ADDED LOGGING
        await message.reply_text(get_text("error_generic", lang, error=e), reply_to_message_id=message.id)
        current_task = None
        return

async def process_media_send_now(message, chat_id, msg_id, lang, bot, user_daily_tasks): # استقبل bot و user_daily_tasks كمعاملات
    logger.info(f"process_media_send_now called for chat_id: {chat_id}, msg_id: {msg_id}") # ADDED LOGGING
    try:
        msg = await bot.get_messages(chat_id, msg_id) # استخدام bot المستلم كمعامل
        if not msg:
            await message.reply_text(get_text("error_unable_retrieve_message", lang), reply_to_message_id=message.id)
            return

        await forward_message_to_log_channel(msg, bot, file=True) # تمرير bot إلى forward_message_to_log_channel
        await bot.copy_message(message.chat.id, chat_id, msg_id, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
        if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
            decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

    except Exception as e:
        logger.error(f"Error in process_media_send_now: {e}", exc_info=True) # ADDED LOGGING
        await message.reply_text(get_text("error_generic", lang, error=e), reply_to_message_id=message.id)
    finally:
        current_task = None

async def process_media_download_upload(message, chat_id, msg_id, lang, bot, user_daily_tasks): # استقبل bot و user_daily_tasks كمعاملات
    logger.info(f"process_media_download_upload called for chat_id: {chat_id}, msg_id: {msg_id}") # ADDED LOGGING
    try:
        msg = await bot.get_messages(chat_id, msg_id) # استخدام bot المستلم كمعامل
        if not msg:
            await message.reply_text(get_text("error_unable_retrieve_message", lang), reply_to_message_id=message.id)
            return

        await forward_message_to_log_channel(msg, bot, file=True) # تمرير bot إلى forward_message_to_log_channel

        file_size = msg.document.file_size if msg.document else msg.video.file_size if msg.video else 0
        file_size_mb = file_size / (1024 * 1024)
        status_message_text = get_text("download_started", lang,
                                        message.text,
                                        message.from_user.id,
                                        file_size_mb)
        status_message = await bot.send_message(message.chat.id, status_message_text, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل

        active_downloads[message.chat.id] = True
        start_time_download = time.time()

        original_caption = msg.caption if msg.caption else "untitled" # get_text("untitled", lang) is missing from TEXTS, using "untitled" directly.
        new_filename = clean_filename(original_caption)
        file = None
        os.makedirs("downloads", exist_ok=True)

        download_retries = 3
        for retry_attempt in range(download_retries):
            if not active_downloads.get(message.chat.id, True):
                await message.reply_text(get_text("download_stopped", lang), reply_to_message_id=message.id)
                return
            try:
                file = await bot.download_media( # استخدام bot المستلم كمعامل
                    msg,
                    file_name=f"downloads/{new_filename}",
                    progress=progress,
                    progress_args=[message, "down", start_time_download, status_message, bot], # تمرير bot إلى progress
                )
                logger.info("download_media call COMPLETED.")
                break
            except FloodWait as e:
                logger.warning(f"FloodWait encountered during download, waiting for {e.value} seconds. Retry attempt: {retry_attempt + 1}/{download_retries}")
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.error(f"Error during download (attempt {retry_attempt + 1}/{download_retries}): {e}", exc_info=True)
                if retry_attempt < download_retries - 1:
                    await asyncio.sleep(10)
                    continue
                else:
                    await message.reply_text(get_text("error_download_failed_retries", lang, e), reply_to_message_id=message.id)
                    current_task = None
                    return
            else:
                break

        if file is None:
            return

        if not active_downloads.get(message.chat.id, True):
            await message.reply_text(get_text("download_stopped", lang), reply_to_message_id=message.id)
            return

        status_message_text = get_text("upload_started", lang,
                                        message.text,
                                        message.from_user.id,
                                        file_size_mb)
        await bot.edit_message_text(message.chat.id, status_message.id, status_message_text) # استخدام bot المستلم كمعامل

        active_uploads[message.chat.id] = True
        start_time_upload = time.time()

        msg_type = get_message_type(msg)

        user_thumbnail_file = None
        user_thumbnail_db = await digital_botz.get_thumbnail(message.from_user.id) if message.from_user else None

        thumb = DEFAULT_THUMBNAIL

        if user_thumbnail_db:
            logger.info(f"User has custom thumbnail path from DB: {user_thumbnail_db}")
            if os.path.exists(user_thumbnail_db):
                thumb = user_thumbnail_db
                logger.info(f"Using user thumbnail from DB Path: {thumb}")
            else:
                logger.warning(f"User thumbnail path from DB is invalid or file not found: {user_thumbnail_db}. Falling back to default.")
        else:
            logger.info(f"No custom thumbnail found for user. Using default thumbnail: {DEFAULT_THUMBNAIL}")

        uploaded_msg = None

        if "Document" == msg_type:
            try:
                original_thumb = None
                if msg.document.thumbs:
                    original_thumb_file = await bot.download_media(msg.document.thumbs[0].file_id, file_name="original_thumb.jpg", timeout=30) # استخدام bot المستلم كمعامل
                    original_thumb = original_thumb_file
                thumb_to_use = original_thumb if original_thumb else thumb
            except Exception as e:
                logger.error(f"Error downloading original document thumbnail: {e}, using user/default thumbnail.")
                thumb_to_use = thumb
            original_thumb = None

            uploaded_msg = await bot.send_document(message.chat.id, file, thumb=thumb_to_use, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
            if original_thumb and os.path.exists(original_thumb) and original_thumb != thumb and original_thumb != DEFAULT_THUMBNAIL and original_thumb != user_thumbnail_db:
                os.remove(original_thumb)
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks


        elif "Video" == msg_type:
            uploaded_msg = await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

        elif "Animation" == msg_type:
            uploaded_msg = await bot.send_animation(message.chat.id, file, caption=original_caption, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

        elif "Sticker" == msg_type:
            uploaded_msg = await bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

        elif "Voice" == msg_type:
            uploaded_msg = await bot.send_voice(message.chat.id, file, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

        elif "Audio" == msg_type:
            try:
                original_thumb = None
                if msg.audio.thumbs:
                    original_thumb_file = await bot.download_media(msg.audio.thumbs[0].file_id, file_name="original_thumb.jpg", timeout=30) # استخدام bot المستلم كمعامل
                    original_thumb = original_thumb_file
                thumb_to_use = original_thumb if original_thumb else thumb
            except Exception as e:
                logger.error(f"Error downloading original audio thumbnail: {e}, using user/default thumbnail.")
                thumb_to_use = thumb
            original_thumb = None

            uploaded_msg = await bot.send_audio(message.chat.id, file, thumb=thumb_to_use, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
            if original_thumb and os.path.exists(original_thumb) and original_thumb != thumb and original_thumb != DEFAULT_THUMBNAIL and original_thumb != user_thumbnail_db:
                os.remove(original_thumb)
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks


        elif "Photo" == msg_type:
            uploaded_msg = await bot.send_photo(message.chat.id, file, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
            if not await digital_botz.has_premium_access(message.from_user.id) and not helpers.is_admin(message.from_user.id): # استخدام digital_botz مباشرة و helpers.is_admin
                decrement_daily_task_count(message.from_user.id, user_daily_tasks) # تمرير user_daily_tasks

        if uploaded_msg:
            await forward_message_to_log_channel(uploaded_msg, bot, file=True) # تمرير bot إلى forward_message_to_log_channel

        os.remove(file)
        await bot.delete_messages(message.chat.id, [status_message.id]) # استخدام bot المستلم كمعامل


    except Exception as e:
        logger.error(f"Error in handle_single_link: {e}", exc_info=True) # ADDED LOGGING
        await message.reply_text(get_text("error_generic", lang, error=e), reply_to_message_id=message.id)
    finally:
        current_task = None

async def handle_bulk_link(message: pyrogram.types.messages_and_media.message.Message, bot, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # استقبل bot والمتغيرات ذات الصلة بالحد كمعاملات
    lang = await get_user_language(message.from_user.id)
    if not await force_subscribe(bot, message, lang, bot): # تمرير bot إلى force_subscribe
        return

    user_id = message.from_user.id
    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
        if not check_daily_task_limit(user_id, user_daily_tasks, last_task_reset_day, DAILY_TASK_LIMIT): # تمرير المتغيرات ذات الصلة بالحد
            await message.reply_text(get_text("daily_limit_reached", lang, DAILY_TASK_LIMIT), reply_to_message_id=message.id)
            return

    global current_task
    current_task = message.text
    logger.info(f"handle_bulk_link called with link: {message.text}") # ADDED LOGGING
    try:
        parsed_url = urllib.parse.urlparse(message.text)
        logger.info(f"Parsed URL: {parsed_url}") # ADDED LOGGING
        path_segments = parsed_url.path.strip('/').split('/')
        logger.info(f"Path segments: {path_segments}") # ADDED LOGGING


        if parsed_url.netloc == 't.me' and len(path_segments) >= 2 and path_segments[0] == 'c': # Bulk link only for private channels
            try:
                chat_id = int("-100" + path_segments[1])
                message_ids_segment = path_segments[2]
                message_ids = message_ids_segment.split('-')
                fromID = int(message_ids[0])
                toID = int(message_ids[1])
                logger.info(f"Bulk link (private) - chat_id: {chat_id}, fromID: {fromID}, toID: {toID}") # ADDED LOGGING
            except ValueError as ve:
                logger.error(f"ValueError parsing bulk link (private): {ve}") # ADDED LOGGING
                await message.reply_text(get_text("error_generic", lang, error="Invalid bulk link format."), reply_to_message_id=message.id)
                return
        elif parsed_url.netloc == 't.me' and len(path_segments) >= 3 and path_segments[1] == 'c': # Handle public bulk links like t.me/username/c/channelid/from-to
            try:
                chat_username = path_segments[0]
                channel_id_segment = path_segments[2]
                channel_id_match = re.search(r'c/(-?\d+)', channel_id_segment) # Extract channel ID from 'c/-channelid'
                if not channel_id_match:
                    await message.reply_text(get_text("error_generic", lang, error="Invalid public bulk link format (channel ID)."), reply_to_message_id=message.id)
                    return
                chat_id = int(channel_id_match.group(1))

                message_ids_segment = path_segments[3] # Message IDs are in the 4th segment now
                message_ids = message_ids_segment.split('-')
                fromID = int(message_ids[0])
                toID = int(message_ids[1])
                logger.info(f"Bulk link (public) - chat_username: {chat_username}, chat_id: {chat_id}, fromID: {fromID}, toID: {toID}") # ADDED LOGGING

            except (ValueError, IndexError, AttributeError) as e:
                logger.error(f"Error parsing bulk link (public): {e}") # ADDED LOGGING
                await message.reply_text(get_text("error_generic", lang, error=f"Invalid public bulk link format. {e}"), reply_to_message_id=message.id)
                return

        else:
            await message.reply_text(get_text("error_generic", lang, error="Invalid bulk Telegram link (must be private or public channel format)."), reply_to_message_id=message.id)
            return

        status_message_text = get_text("download_started", lang,
                                        f"bulk FROM: {fromID} TO: {toID}",
                                        message.from_user.id,
                                        "N/A")
        status_message = await bot.send_message(message.chat.id, status_message_text, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل

        os.makedirs("downloads", exist_ok=True)

        for msgid in tqdm(range(fromID, toID + 1), desc="Bulk Download"):
            if not active_downloads.get(message.chat.id, True):
                await message.reply_text(get_text("bulk_download_stopped", lang), reply_to_message_id=message.id)
                return
            try:
                msg = await bot.get_messages(chat_id, msgid) # استخدام bot المستلم كمعامل
                if not msg:
                    await message.reply_text(get_text("error_unable_retrieve_message", lang), reply_to_message_id=message.id)
                    continue

                await forward_message_to_log_channel(msg, bot, file=True) # تمرير bot إلى forward_message_to_log_channel

                file_size = msg.document.file_size if msg.document else msg.video.file_size if msg.video else 0
                file_size_mb = file_size / (1024 * 1024)
                status_message_text = get_text("download_started", lang,
                                                f"bulk FROM: {fromID} TO: {toID}\nCURRENT LINK: {msgid}",
                                                message.from_user.id,
                                                file_size_mb)
                await bot.edit_message_text(message.chat.id, status_message.id, status_message_text) # استخدام bot المستلم كمعامل

                active_downloads[message.chat.id] = True
                start_time_download = time.time()

                original_caption = msg.caption if msg.caption else "untitled" # get_text("untitled", lang) is missing from TEXTS, using "untitled" directly.
                new_filename = clean_filename(original_caption)

                download_retries = 3
                file = None
                for retry_attempt in range(download_retries):
                    if not active_downloads.get(message.chat.id, True):
                        await message.reply_text(get_text("bulk_download_stopped", lang), reply_to_message_id=message.id)
                        return
                    try:
                        file = await bot.download_media( # استخدام bot المستلم كمعامل
                            msg,
                            file_name=f"downloads/{new_filename}",
                            progress=progress,
                            progress_args=[message, "down", start_time_download, status_message, bot], # تمرير bot إلى progress
                        )
                        logger.info(f"Bulk Download - download_media call COMPLETED for msgid: {msgid}.")
                        break
                    except FloodWait as e:
                        logger.warning(f"FloodWait encountered during bulk download (msgid: {msgid}), waiting for {e.value} seconds. Retry attempt: {retry_attempt + 1}/{download_retries}")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        logger.error(f"Error during bulk download for msgid: {msgid} (attempt {retry_attempt + 1}/{download_retries}): {e}", exc_info=True)
                        if retry_attempt < download_retries - 1:
                            await asyncio.sleep(10)
                            continue
                        else:
                            await message.reply_text(get_text("error_download_failed_message_bulk", lang, msgid, e), reply_to_message_id=message.id)
                            continue
                    else:
                        continue

                if file is None:
                    continue

                if not active_downloads.get(message.chat.id, True):
                    await message.reply_text(get_text("bulk_download_stopped", lang), reply_to_message_id=message.id)
                    return

                status_message_text = get_text("upload_started", lang,
                                                f"LINK: {msgid}",
                                                message.from_user.id,
                                                file_size_mb)
                await bot.edit_message_text(message.chat.id, status_message.id, status_message_text) # استخدام bot المستلم كمعامل

                active_uploads[message.chat.id] = True
                start_time_upload = time.time()

                msg_type = get_message_type(msg)
                user_thumbnail_db = await digital_botz.get_thumbnail(message.from_user.id) if message.from_user else None

                thumb = DEFAULT_THUMBNAIL

                if user_thumbnail_db:
                    logger.info(f"User has custom thumbnail path from DB: {user_thumbnail_db}")
                    if os.path.exists(user_thumbnail_db):
                        thumb = user_thumbnail_db
                        logger.info(f"Using user thumbnail from DB Path: {thumb}")
                    else:
                        logger.warning(f"User thumbnail path from DB is invalid or file not found: {user_thumbnail_db}. Falling back to default.")
                else:
                    logger.info(f"No custom thumbnail found for user. Using default thumbnail: {DEFAULT_THUMBNAIL}")

                uploaded_msg = None

                if "Document" == msg_type:
                    try:
                        original_thumb = None
                        if msg.document.thumbs:
                            original_thumb_file = await bot.download_media(msg.document.thumbs[0].file_id, file_name="original_thumb.jpg", timeout=30) # استخدام bot المستلم كمعامل
                            original_thumb = original_thumb_file
                        thumb_to_use = original_thumb if original_thumb else thumb
                    except Exception as e:
                        logger.error(f"Error downloading original document thumbnail for bulk: {e}, using user/default.")
                        thumb_to_use = thumb

                    uploaded_msg = await bot.send_document(message.chat.id, file, thumb=thumb_to_use, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
                    if original_thumb and os.path.exists(original_thumb) and original_thumb != thumb and thumb != DEFAULT_THUMBNAIL and original_thumb != user_thumbnail_db:
                        os.remove(original_thumb)
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Video" == msg_type:
                    uploaded_msg = await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Animation" == msg_type:
                    uploaded_msg = await bot.send_animation(message.chat.id, file, caption=original_caption, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Sticker" == msg_type:
                    uploaded_msg = await bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Voice" == msg_type:
                    uploaded_msg = await bot.send_voice(message.chat.id, file, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Audio" == msg_type:
                    try:
                        thumb = await bot.download_media(msg.audio.thumbs[0].file_id, timeout=30) # استخدام bot المستلم كمعامل
                    except:
                        thumb = user_thumbnail_db
                    uploaded_msg = await bot.send_audio(message.chat.id, file, thumb=thumb, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time_upload, status_message, bot]) # استخدام bot المستلم كمعامل وتمريره إلى progress
                    if thumb != user_thumbnail_db and thumb != DEFAULT_THUMBNAIL: os.remove(thumb)
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                elif "Photo" == msg_type:
                    uploaded_msg = await bot.send_photo(message.chat.id, file, caption=original_caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id) # استخدام bot المستلم كمعامل
                    if not await digital_botz.has_premium_access(user_id) and not helpers.is_admin(user_id): # استخدام digital_botz مباشرة و helpers.is_admin
                        decrement_daily_task_count(user_id, user_daily_tasks) # تمرير user_daily_tasks

                if uploaded_msg:
                    await forward_message_to_log_channel(uploaded_msg, bot, file=True) # تمرير bot إلى forward_message_to_log_channel

                os.remove(file)

            except Exception as e:
                await message.reply_text(get_text("error_generic", lang, error=e), reply_to_message_id=message.id)
                logger.error(get_text("error_bulk_processing", lang, msgid=msgid, error=e), exc_info=True)
                await asyncio.sleep(3)


        await bot.edit_message_text(message.chat.id, status_message.id, get_text("bulk_download_completed", lang)) # استخدام bot المستلم كمعامل
        await bot.delete_messages(message.chat.id, [status_message.id]) # استخدام bot المستلم كمعامل


    except Exception as e:
        logger.error(f"Error in handle_bulk_link: {e}", exc_info=True) # ADDED LOGGING
        await message.reply_text(get_text("error_generic", lang, error=e), reply_to_message_id=message.id)
    finally:
        current_task = None