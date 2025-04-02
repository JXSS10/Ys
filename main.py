import os
import re
import yt_dlp
import ffmpeg # For metadata and thumbnails
import asyncio
import math
import time
import logging
import http.cookiejar
from io import StringIO
from datetime import datetime
from typing import Optional, List # Import Optional and List
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
)
from pyrogram.errors import (
    MessageNotModified, MessageIdInvalid, FloodWait
)
from pyrogram.enums import ChatAction, ParseMode

# --- 1. Configuration and Setup ---

# Configure Logging
logging.basicConfig(
    level=logging.INFO, # Change to DEBUG for more verbose logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # Log to console
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING) # Reduce pyrogram's verbosity
YTUB_COOKIES = """
Netscape HTTP Cookie File
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	TRUE	1758115994	VISITOR_INFO1_LIVE	MHCsPCRDwfQ
.youtube.com	TRUE	/	TRUE	1758115994	VISITOR_PRIVACY_METADATA	CgJFRxIEGgAgMg%3D%3D
.youtube.com	TRUE	/	TRUE	1756380934	VISITOR_INFO1_LIVE	0gttXPJu8Rw
.youtube.com	TRUE	/	TRUE	1756380934	VISITOR_PRIVACY_METADATA	CgJFRxIEGgAgZA%3D%3D
.youtube.com	TRUE	/	TRUE	1756472193	VISITOR_INFO1_LIVE	iHXGKxm-y3Y
.youtube.com	TRUE	/	TRUE	1756472193	VISITOR_PRIVACY_METADATA	CgJFRxIEGgAgMg%3D%3D
.youtube.com	TRUE	/	TRUE	1756472193	__Secure-ROLLOUT_TOKEN	CND5pPOe0-X6bxDZwqmY5eiLAxjC6aeNueuLAw%3D%3D
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-ROLLOUT_TOKEN	CJ-g9eG-qPCzaRCXsuqR5eiLAxi1yNKaueuLAw%3D%3D
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-3PSIDCC	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c3i82yK7
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-3PSID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6clU6P6L
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-3PAPISID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c0jX77-
.youtube.com	TRUE	/	TRUE	1756472221	__Secure-SSO-SID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c6y885D
.youtube.com	TRUE	/	TRUE	1756472221	SID	A7i_DTjG5o8h1HS2Xm1XP9Yc9v9t697GS4k1NfTf98Ob80wJp0_fYSgQyY-b-oU-lJ_0g.
.youtube.com	TRUE	/	TRUE	1756472221	APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1756472221	HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1756472221	SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1756380954	dextp	60-1-1740828946212|477-1-1740828946805|1123-1-1740828947921|903-1-1740828948816|1957-1-1740828949766|22052-1-1740828951921|30064-1-1740828952741|161033-1-1740828954931
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-YEC	CgYKCQgBEgZ5bRIiEglsS1JKS2tXZ1lZEgZ5bRIiEqoHEglsS1JKS2tXZ1laSAIyAhpHEglzS1JKS2tXZ1lZEglzS1JKS2tXZ1la
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-3PSIDCC	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c3i82yK7
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-3PSID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6clU6P6L
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-3PAPISID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c0jX77-
.youtube.com	TRUE	/	TRUE	1756380954	__Secure-SSO-SID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c6y885D
.youtube.com	TRUE	/	TRUE	1756380954	SID	A7i_DTjG5o8h1HS2Xm1XP9Yc9v9t697GS4k1NfTf98Ob80wJp0_fYSgQyY-b-oU-lJ_0g.
.youtube.com	TRUE	/	TRUE	1756380954	APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1756380954	HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1756380954	SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1756724139	__Secure-ROLLOUT_TOKEN	CJyju6_v2JXvbxDc0MvW4_KLAxjc0MvW4_KLAw%3D%3D
.youtube.com	TRUE	/	TRUE	1756724139	VISITOR_INFO1_LIVE	Wm7m-MTtdT8
.youtube.com	TRUE	/	TRUE	1756724139	VISITOR_PRIVACY_METADATA	CgJFRxIEGgAgWw%3D%3D
.youtube.com	TRUE	/	TRUE	1758115994	__Secure-ROLLOUT_TOKEN	CJj_tYXP9LfSIRDvx-vOsOiLAxjNy67fpJuMAw%3D%3D
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-ROLLOUT_TOKEN	CKiPqsqbptWn6QEQnqCNsLy3jAMYt_zBw7y3jAM%3D
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-YEC	CgYKCQgBEgZ5bRIiEglzS1JKS2tXZ1laEgZ5bRIiEqoHEglzS1JKS2tXZ1laSAIyAhpHEglzS1JKS2tXZ1lZEglzS1JKS2tXZ1la
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-3PSIDCC	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c3i82yK7
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-3PSID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6clU6P6L
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-3PAPISID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c0jX77-
.youtube.com	TRUE	/	TRUE	1759084452	__Secure-SSO-SID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c6y885D
.youtube.com	TRUE	/	TRUE	1759084452	SID	A7i_DTjG5o8h1HS2Xm1XP9Yc9v9t697GS4k1NfTf98Ob80wJp0_fYSgQyY-b-oU-lJ_0g.
.youtube.com	TRUE	/	TRUE	1759084452	APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1759084452	HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1759084452	SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1759094418	VISITOR_INFO1_LIVE	MyOIeUxTDOo
.youtube.com	TRUE	/	TRUE	1759094418	VISITOR_PRIVACY_METADATA	CgJFRxIEGgAgTg%3D%3D
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-YEC	CgYKCQgBEgZ5bRIiEglzS1JKS2tXZ1laEgZ5bRIiEqoHEglzS1JKS2tXZ1laSAIyAhpHEglzS1JKS2tXZ1lZEglzS1JKS2tXZ1la
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-3PSIDCC	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c3i82yK7
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-3PSID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6clU6P6L
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-3PAPISID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c0jX77-
.youtube.com	TRUE	/	TRUE	1759094418	__Secure-SSO-SID	ACAQQw8yAAHJi6D5kw6_tg9y_9sV-o39r82w1b4_61lYJ9z8i7k5eJcvlY6c6y885D
.youtube.com	TRUE	/	TRUE	1759094418	SID	A7i_DTjG5o8h1HS2Xm1XP9Yc9v9t697GS4k1NfTf98Ob80wJp0_fYSgQyY-b-oU-lJ_0g.
.youtube.com	TRUE	/	TRUE	1759094418	APISID	AL-QmvO3Wwc4iVpE/Ahc7msFwQj0
.youtube.com	TRUE	/	TRUE	1759094418	HSID	A7i_DTjG5o8h1HS2X
.youtube.com	TRUE	/	TRUE	1759094418	SSID	A0Sg1_Zpvt1_fM6g0
.youtube.com	TRUE	/	TRUE	1759353620	NID	522=wzsa4BonkkvN7Z0TBfJjXPUXPm4mf6u2uljrV1FsqBrwjB55RhtQdldQM6pu1uj0uZJtQKfBsktY-EKVAIY2GbNxujDTrHzJkyniP3SV0X4fqY0xgVmf1cL3dhXOIR0q_xMOs1vXAE88GTJ3fZUlhAwPZ5alSABUzWiV3O7ZMJ2iHa-4ggO_fFo-KHcEtNpEt9bFmeSuy7Jd2CIpTCUGu5Wkv2_NnhFcxOAqcSquPuU4qnGfzLAQgTRPhH831lOBGui3_i80Vcsh
.youtube.com	TRUE	/	TRUE	1743544218	GPS	1
.youtube.com	TRUE	/	TRUE	0	YSC	FdDjnHg1lag
"""
# Environment Variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YTUB_COOKIES_CONTENT=YTUB_COOKIES
# Validate Essential Config
if not all([API_ID, API_HASH, BOT_TOKEN]):
    LOGGER.critical("FATAL ERROR: API_ID, API_HASH, or BOT_TOKEN is missing!")
    exit(1) # Exit if essential config is missing
try:
    API_ID = int(API_ID)
except ValueError:
    LOGGER.critical("FATAL ERROR: API_ID must be an integer!")
    exit(1)

# Constants
DOWNLOAD_FOLDER = "./downloads/"
MAX_TG_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024 # 2GB limit for Telegram
SESSION_TIMEOUT = 1800 # Timeout for inactive sessions (30 minutes)

# Global Session Dictionary (In-memory storage)
# Format: {user_id: {'timestamp': time.time(), 'data': {...}}}
user_sessions = {}

# Create Download Folder
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    LOGGER.info(f"Created download folder: {DOWNLOAD_FOLDER}")

# --- 2. Utility Functions ---

def load_cookies():
    """Loads cookies from the YTUB_COOKIES environment variable."""
    cookie_jar = http.cookiejar.MozillaCookieJar()
    if YTUB_COOKIES_CONTENT and YTUB_COOKIES_CONTENT.strip():
        try:
            cookie_jar.load(StringIO(YTUB_COOKIES_CONTENT), ignore_discard=True, ignore_expires=True)
            LOGGER.debug("Cookies loaded successfully from variable.")
            return cookie_jar
        except Exception as e:
            LOGGER.warning(f"Error loading cookies from variable: {e}. Proceeding without cookies.")
            return None
    else:
        LOGGER.debug("YTUB_COOKIES variable is empty or missing. Proceeding without cookies.")
        return None

def format_bytes(size):
    """Formats a size in bytes into a human-readable string."""
    if size is None: return "N/A"
    try:
        size = float(size)
        if size == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = max(0, min(len(size_name) - 1, int(math.floor(math.log(size, 1024)))))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return f"{s} {size_name[i]}"
    except (ValueError, TypeError, OverflowError) as e:
        LOGGER.warning(f"Error formatting bytes ({size}): {e}")
        return "N/A"

def td_format(seconds):
    """Formats duration in seconds to a human-readable string (H M S)."""
    if seconds is None: return "N/A"
    try:
        seconds = int(float(seconds))
        if seconds < 0: return "N/A"
        periods = [('ساعة', 3600), ('دقيقة', 60), ('ثانية', 1)]
        strings = []
        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value > 0: strings.append(f"{period_value} {period_name}")
        if not strings: return "أقل من ثانية" if seconds < 1 else "0 ثوان"
        return "، ".join(strings)
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Error formatting duration ({seconds}): {e}")
        return "غير معروف"

def progress_bar_generator(percentage, bar_length=15):
    """Generates a simple text-based progress bar string."""
    try:
        percentage = max(0.0, min(1.0, float(percentage)))
        completed = int(round(bar_length * percentage))
        return '█' * completed + '░' * (bar_length - completed)
    except ValueError:
        return '░' * bar_length

async def cleanup_session(user_id, message: Message = None, text="انتهت صلاحية الجلسة أو تم إلغاؤها."):
    """Removes user session and optionally edits the status message."""
    if user_id in user_sessions:
        session_message_id = user_sessions[user_id].get('data', {}).get('status_message_id')
        del user_sessions[user_id]
        LOGGER.info(f"Session cleaned for user {user_id}")
        if message and session_message_id == message.id:
            try:
                await message.edit_text(text, reply_markup=None)
            except (MessageIdInvalid, MessageNotModified):
                pass # Message already gone or unchanged
            except Exception as e:
                 LOGGER.warning(f"Error editing message during session cleanup for user {user_id}: {e}")
        # Clean download files potentially associated with this user (more robust cleanup needed for shared folder)
        # For now, we clean files after upload attempt in the main flow

async def edit_status_message(client: Client, session_data: dict, text: str, reply_markup=None):
    """Safely edits the status message associated with a session."""
    message_id = session_data.get('status_message_id')
    chat_id = session_data.get('chat_id')
    if not message_id or not chat_id:
        LOGGER.warning("Attempted to edit status message but ID or Chat ID is missing in session.")
        return
    try:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return True
    except MessageNotModified:
        pass # No change needed
    except MessageIdInvalid:
        LOGGER.warning(f"Message {message_id} is invalid or deleted. Cannot edit.")
        session_data['status_message_id'] = None # Stop trying to edit
        return False
    except FloodWait as fw:
        LOGGER.warning(f"FloodWait for {fw.value}s while editing status message.")
        await asyncio.sleep(fw.value + 1)
        return await edit_status_message(client, session_data, text, reply_markup) # Retry after wait
    except Exception as e:
        LOGGER.error(f"Failed to edit status message {message_id}: {e}", exc_info=True)
        return False

# --- 3. YouTube Interaction Functions ---

async def get_youtube_info(url: str) -> dict:
    """Fetches video info using yt-dlp. Returns info dict or {'error': msg}."""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'retries': 3,
        'extract_flat': 'discard_in_playlist',
        'dump_single_json': True,
        'cookiejar': load_cookies(),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    }
    # Remove cookiejar if None
    if ydl_opts['cookiejar'] is None:
        del ydl_opts['cookiejar']

    LOGGER.info(f"Fetching info for URL: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Use asyncio.to_thread for the blocking network call
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            LOGGER.info(f"Info fetched successfully for {url.split('&')[0]}")
            return info_dict
    except yt_dlp.utils.DownloadError as e:
        LOGGER.warning(f"yt-dlp info extraction failed: {e}")
        # Basic error mapping
        error_str = str(e).lower()
        if "video unavailable" in error_str: return {"error": "الفيديو غير متاح."}
        if "private video" in error_str: return {"error": "هذا الفيديو خاص."}
        if "confirm your age" in error_str: return {"error": "هذا المحتوى يتطلب تسجيل الدخول وتأكيد العمر."}
        if "premiere" in error_str: return {"error": "هذا الفيديو عرض أول ولم يبدأ بعد."}
        if "is live" in error_str: return {"error": "البث المباشر غير مدعوم حاليًا للتحميل."}
        if "http error 403" in error_str: return {"error": "خطأ 403: الوصول مرفوض (قد يكون مقيدًا أو يتطلب كوكيز)."}
        if "http error 404" in error_str: return {"error": "خطأ 404: الفيديو غير موجود."}
        if "invalid url" in error_str: return {"error": "الرابط غير صالح أو غير مدعوم."}
        if "unable to download webpage" in error_str: return {"error": "تعذر الوصول إلى الرابط."}
        return {"error": f"فشل جلب المعلومات: {str(e)[:150]}"} # Truncated generic error
    except Exception as e:
        LOGGER.error(f"General exception during info fetching: {e}", exc_info=True)
        return {"error": f"خطأ غير متوقع في جلب المعلومات: {e}"}

async def download_progress_hook_async(d: dict, status_message: Message, session_data: dict):
    """Async progress hook to update Telegram status message."""
    user_id = session_data.get('user_id')
    if not user_id: return # Should not happen if session is valid

    # Throttle updates
    now = time.time()
    last_update = session_data.get('last_download_update_time', 0)
    if d['status'] not in ['finished', 'error'] and (now - last_update < 1.5):
        return
    session_data['last_download_update_time'] = now

    text = ""
    try:
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes is not None:
                percentage = downloaded_bytes / total_bytes
                speed_str = d.get('_speed_str', "N/A")
                eta_str = d.get('_eta_str', "N/A")
                filename = d.get('info_dict', {}).get('title', os.path.basename(d.get('filename', '')) )[:50]
                pl_info = f" (مقطع {d.get('playlist_index')}/{d.get('playlist_count')})" if d.get('playlist_index') else ""

                text = (
                    f"{session_data.get('base_caption', '...')}\n\n"
                    f"**⏳ جاري التحميل{pl_info}:**\n"
                    f"`{filename}...`\n"
                    f"📦 {progress_bar_generator(percentage)} ({percentage*100:.1f}%)\n"
                    f"💾 {format_bytes(downloaded_bytes)} / {format_bytes(total_bytes)}\n"
                    f"🚀 السرعة: {speed_str} | ⏳ المتبقي: {eta_str}"
                )

        elif d['status'] == 'finished':
             # Update only if it's the last item or single download
            is_last = not d.get('playlist_index') or (d.get('playlist_index') == d.get('playlist_count'))
            if is_last:
                 text = f"{session_data.get('base_caption', '...')}\n\n✅ اكتمل التحميل. جاري المعالجة والرفع..."
                 # Update base caption for upload phase (optional)
                 session_data['base_caption'] = f"✅ {session_data.get('title', 'اكتمل التحميل')}"
            else:
                 LOGGER.info(f"Playlist item {d.get('playlist_index')}/{d.get('playlist_count')} finished.")
                 return # Don't edit message for intermediate playlist items

        elif d['status'] == 'error':
            LOGGER.error(f"yt-dlp hook reported error for user {user_id}: {d.get('_error_cause', 'Unknown')}")
            # Error is handled by the main download function's return value
            return # Don't edit here, let the main function handle failure display

        if text:
            await edit_status_message(None, session_data, text) # Pass client=None if not available here

    except Exception as e:
        LOGGER.error(f"Error in download progress hook for user {user_id}: {e}", exc_info=True)

# Wrapper for yt-dlp hook (since it's called synchronously)
def download_progress_hook_wrapper(d: dict):
    """Wrapper to run the async hook in the event loop."""
    session_data = d.get('session_data') # We need to pass session data into ydl_opts
    status_message = d.get('status_message_obj') # Pass the message object
    if session_data and status_message:
        try:
            # Ensure there's a running event loop (might be needed if yt-dlp runs in a separate thread)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                 asyncio.ensure_future(download_progress_hook_async(d, status_message, session_data))
            else:
                 # Fallback if no loop (less ideal) - might block
                 # Or log a warning: LOGGER.warning("No running event loop for progress hook")
                 pass
        except RuntimeError:
             # LOGGER.warning("No running event loop found for progress hook.")
             pass # Ignore if no loop is readily available
    else:
        LOGGER.warning("Session data or status message missing in progress hook wrapper.")


def do_youtube_download(url: str, format_selector: str, media_type: str, session_data: dict, status_message: Message) -> (Optional[List[str]], Optional[str]): # Modified return type
    """
    Performs the download using yt-dlp in a blocking manner.
    Returns (list_of_file_paths, None) on success, or (None, error_message) on failure.
    """
    user_id = session_data.get('user_id', 'UnknownUser')
    LOGGER.info(f"Starting download for user {user_id}, type: {media_type}, format: '{format_selector}'")

    base_title = re.sub(r'[\\/*?:"<>|]', "", session_data.get('title', 'youtube_download'))[:100]
    output_template_base = os.path.join(DOWNLOAD_FOLDER, f"{user_id}_{base_title}_{int(time.time())}")

    final_expected_ext = 'mp3' if media_type == 'audio' else 'mp4'
    output_template = f'{output_template_base}.%(ext)s'
    postprocessors = []

    if media_type == 'audio':
        output_template = f'{output_template_base}.mp3' # Expect mp3
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })

    ydl_opts = {
        'format': format_selector,
        'outtmpl': output_template,
        'progress_hooks': [download_progress_hook_wrapper],
        'postprocessors': postprocessors,
        'nocheckcertificate': True,
        'prefer_ffmpeg': True,
        'retries': 5,
        'fragment_retries': 5,
        'http_chunk_size': 10 * 1024 * 1024,
        'merge_output_format': 'mp4',
        'cookiejar': load_cookies(),
        'verbose': False, # Keep False unless debugging yt-dlp itself
        'quiet': False, # Need False for progress hooks
        'ignoreerrors': True, # Attempt to continue playlists on error
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        },
        # Pass necessary data to the hook wrapper
        'session_data': session_data,
        'status_message_obj': status_message,
    }
    if ydl_opts['cookiejar'] is None: del ydl_opts['cookiejar']

    downloaded_files = []
    final_error_message = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            LOGGER.debug(f"Running yt-dlp for user {user_id} with opts: { {k: v for k, v in ydl_opts.items() if k not in ['session_data', 'status_message_obj']} }") # Log opts without sensitive data
            info_dict = ydl.extract_info(url, download=True) # Blocking call
            LOGGER.info(f"yt-dlp finished for user {user_id}")

            # --- Locate downloaded file(s) ---
            is_playlist = 'entries' in info_dict and info_dict['entries'] is not None

            if is_playlist:
                LOGGER.debug(f"Processing playlist results for user {user_id} ({len(info_dict.get('entries',[]))} entries)")
                for entry in info_dict.get('entries', []):
                    if not entry: continue # Skip potential None entries on error
                    filepath = None
                    req_dl = entry.get('requested_downloads')
                    if req_dl: filepath = req_dl[-1].get('filepath') # Most reliable path after processing

                    if filepath and os.path.exists(filepath):
                        downloaded_files.append(filepath)
                        LOGGER.debug(f"Found playlist file for user {user_id} via requested_downloads: {filepath}")
                    else: # Fallback construction (less reliable)
                         entry_title = re.sub(r'[\\/*?:"<>|]', "", entry.get('title','entry'))[:50]
                         constructed_base = os.path.join(DOWNLOAD_FOLDER, f"{user_id}_{entry_title}") # Need a unique base per entry
                         expected_path = f"{constructed_base}.{final_expected_ext}" # Simplified fallback path
                         # Glob might be safer here if filenames aren't exact
                         possible_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(f"{user_id}_{entry_title}") and f.endswith(f".{final_expected_ext}")]
                         if possible_files:
                              found_path = os.path.join(DOWNLOAD_FOLDER, possible_files[0])
                              if os.path.exists(found_path):
                                   downloaded_files.append(found_path)
                                   LOGGER.debug(f"Found playlist file for user {user_id} via fallback glob: {found_path}")
                              else:
                                   LOGGER.warning(f"File missing for playlist entry: {entry.get('title','?')}")
                         else:
                              LOGGER.warning(f"Cannot find file for playlist entry: {entry.get('title','?')}")


            else: # Single item
                LOGGER.debug(f"Processing single item result for user {user_id}")
                filepath = None
                req_dl = info_dict.get('requested_downloads')
                if req_dl: filepath = req_dl[-1].get('filepath')

                if filepath and os.path.exists(filepath):
                    downloaded_files.append(filepath)
                    LOGGER.debug(f"Found single file for user {user_id} via requested_downloads: {filepath}")
                else: # Fallback construction
                     expected_path = f"{output_template_base}.{final_expected_ext}"
                     if os.path.exists(expected_path):
                         downloaded_files.append(expected_path)
                         LOGGER.debug(f"Found single file for user {user_id} via constructed path: {expected_path}")
                     else: # Last resort: Glob based on base name
                        possible_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(os.path.basename(output_template_base)) and f.endswith(f".{final_expected_ext}")]
                        if possible_files:
                              found_path = os.path.join(DOWNLOAD_FOLDER, possible_files[0])
                              if os.path.exists(found_path):
                                   downloaded_files.append(found_path)
                                   LOGGER.debug(f"Found single file for user {user_id} via fallback glob: {found_path}")
                              else:
                                   LOGGER.error(f"Could not find final file for user {user_id} (single).")
                                   final_error_message = "لم يتم العثور على الملف النهائي بعد المعالجة."
                        else:
                            LOGGER.error(f"Could not find final file for user {user_id} (single).")
                            final_error_message = "لم يتم العثور على الملف النهائي بعد المعالجة."

    except yt_dlp.utils.DownloadError as e:
        LOGGER.error(f"yt-dlp download failed for user {user_id}: {e}")
        # Basic error mapping (same as info fetch) - can be expanded
        error_str = str(e).lower()
        if "video unavailable" in error_str: final_error_message = "الفيديو غير متاح."
        elif "private video" in error_str: final_error_message = "هذا الفيديو خاص."
        # ... (add other specific errors) ...
        else: final_error_message = f"فشل التحميل: {str(e)[:150]}"
    except Exception as e:
        LOGGER.error(f"General exception during download for user {user_id}: {e}", exc_info=True)
        final_error_message = f"حدث خطأ غير متوقع أثناء التحميل: {e}"

    # Final check
    valid_files = [f for f in downloaded_files if os.path.exists(f)]
    if not valid_files and not final_error_message:
        LOGGER.error(f"Download finished for user {user_id} but no valid files found and no error reported.")
        final_error_message = "فشل التحميل لسبب غير معروف ولم يتم العثور على ملفات."

    if final_error_message:
        return None, final_error_message
    else:
        return valid_files, None

# --- 4. Telegram Interaction Functions ---

def create_media_type_selection(info_dict: dict) -> (str, InlineKeyboardMarkup):
    """Creates caption and buttons for selecting media type."""
    title = info_dict.get('title', 'غير متوفر')
    channel = info_dict.get('channel') or info_dict.get('uploader', 'غير معروف')
    duration = td_format(info_dict.get('duration'))
    is_playlist = info_dict.get('_type') == 'playlist' or \
                  (isinstance(info_dict.get('entries'), list) and len(info_dict['entries']) > 0)
    item_count = len(info_dict['entries']) if is_playlist and info_dict.get('entries') else 1

    caption = f"**{title}**\n\n"
    if channel: caption += f"📺 **القناة:** {channel}\n"
    if is_playlist:
        caption += f"🔢 **عدد المقاطع:** {item_count}\n"
    elif duration != "N/A":
        caption += f"⏱️ **المدة:** {duration}\n"
    # Add other details if needed (views, date etc.)

    caption = caption[:800] + f"\n\n🔧 **اختر نوع التحميل المطلوب:**"

    buttons = [
        [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
        [InlineKeyboardButton("إلغاء ❌", callback_data="cancel_session")]
    ]
    markup = InlineKeyboardMarkup(buttons)
    return caption, markup

def create_format_selection(info_dict: dict, media_type: str) -> (Optional[str], Optional[InlineKeyboardMarkup]): # Modified return type hints
    """Creates text and buttons for selecting download format/quality."""
    formats = info_dict.get('formats', [])
    if not formats:
        return "لم يتم العثور على صيغ متاحة.", None

    buttons = []
    text = ""

    if media_type == 'video':
        text = "🎬 اختر جودة الفيديو المطلوبة:"
        # Simplified tier logic (can be expanded as before)
        # Find best available for each tier preference
        tiers = {'low': None, 'medium': None, 'high': None}
        found_formats = {} # height: format_info

        for f in formats:
             h = f.get('height')
             if h and f.get('vcodec') != 'none':
                 # Simple selection: store the first one found per height (yt-dlp usually lists better first)
                 # More complex logic (like previous versions) can be re-added here if needed
                 if h not in found_formats:
                      found_formats[h] = f

        sorted_heights = sorted(found_formats.keys(), reverse=True)

        # Assign to tiers (simplified)
        for h in sorted_heights:
            if h >= 1080 and not tiers['high']: tiers['high'] = found_formats[h]
            if h >= 720 and not tiers['medium']: tiers['medium'] = found_formats[h] # Can overlap with high if only >720 exists
            if h <= 480 and not tiers['low']: tiers['low'] = found_formats[h] # Takes highest available <= 480p

        # Create buttons
        tier_map = {"low": "ضعيفة (<= 480p)", "medium": "متوسطة (~720p)", "high": "عالية (>= 1080p)"}
        for tier, name in tier_map.items():
             fmt = tiers.get(tier)
             if fmt:
                 size = format_bytes(fmt.get('filesize') or fmt.get('filesize_approx'))
                 label = f"{name} - {fmt.get('height')}p ({fmt.get('ext')}) {f'({size})' if size != 'N/A' else ''}"
                 buttons.append([InlineKeyboardButton(label, callback_data=f"format_video_{tier}")])

    elif media_type == 'audio':
        text = "🔉 اختر جودة الصوت المطلوبة:"
        audio_formats = sorted(
            [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'],
            key=lambda x: x.get('abr', 0), reverse=True
        )
        # Fallback: include combined if no audio-only
        if not audio_formats:
            audio_formats = sorted(
                [f for f in formats if f.get('acodec') != 'none'],
                key=lambda x: x.get('abr', 0), reverse=True
            )

        if not audio_formats: return "لم يتم العثور على صيغ صوتية.", None

        buttons.append([InlineKeyboardButton("أفضل جودة صوت 🏆 (تلقائي)", callback_data="format_audio_best")])
        added_labels = set()
        count = 0
        for f in audio_formats:
            if count >= 5: break # Limit options
            fid = f.get('format_id')
            if not fid: continue
            abr = f.get('abr')
            codec = f.get('acodec','').replace('mp4a.40.2', 'aac')
            ext = f.get('ext')
            size = format_bytes(f.get('filesize') or f.get('filesize_approx'))
            label = f"~{abr:.0f}k {codec} ({ext}) {f'({size})' if size != 'N/A' else ''}" if abr else f"{codec} ({ext}) {f'({size})' if size != 'N/A' else ''}"
            if label not in added_labels:
                 buttons.append([InlineKeyboardButton(label, callback_data=f"format_audio_{fid}")])
                 added_labels.add(label)
                 count += 1

    if not buttons:
        return f"لم يتم العثور على صيغ مناسبة لـ {media_type}.", None

    buttons.append([InlineKeyboardButton("رجوع ↩️", callback_data="back_to_type"), InlineKeyboardButton("إلغاء ❌", callback_data="cancel_session")])
    markup = InlineKeyboardMarkup(buttons)
    return text, markup

def get_format_selector(callback_data: str) -> (Optional[str], Optional[str]): # Modified return type hints
    """Determines the yt-dlp format selector string based on callback data."""
    parts = callback_data.split('_', 2)
    if len(parts) < 3: return None, None # Invalid format

    f_type, media, selection = parts # e.g., format, video, high OR format, audio, best

    if media == 'video':
        tier = selection
        if tier == "low": return "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]", "video"
        if tier == "medium": return "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720]/bestvideo[height<=720]+bestaudio/best[height<=720]", "video"
        if tier == "high": return "bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=1080]+bestaudio/best[height>=1080]/bestvideo[height=720]+bestaudio/best[height=720]/best", "video"
    elif media == 'audio':
        if selection == "best": return "bestaudio/best", "audio"
        # Assume selection is a format_id
        return selection, "audio"

    return None, None # Unknown type

async def upload_progress_hook(current, total, client, status_message, session_data, file_info):
    """Async progress hook for Telegram uploads."""
    user_id = session_data.get('user_id')
    if not user_id: return

    now = time.time()
    last_update = session_data.get('last_upload_update_time', 0)
    if now - last_update < 1.5: return
    session_data['last_upload_update_time'] = now

    try:
        percentage = current / total if total > 0 else 0
        base_caption = session_data.get('base_caption', '...') # Should be updated after download
        fname = file_info.get('name', 'file')[:50]
        findex = file_info.get('index', 0)
        ftotal = file_info.get('total', 1)
        pl_info = f" (ملف {findex}/{ftotal})" if ftotal > 1 else ""

        text = (
            f"{base_caption}\n\n"
            f"**⬆️ جاري الرفع{pl_info}:**\n"
            f"`{fname}...`\n"
            f" {progress_bar_generator(percentage)} ({percentage*100:.1f}%)\n"
            f" {format_bytes(current)} / {format_bytes(total)}"
        )
        await edit_status_message(client, session_data, text)

    except Exception as e:
        LOGGER.error(f"Error in upload progress hook for user {user_id}: {e}", exc_info=True)

async def extract_metadata_and_thumb(file_path: str, media_type: str, fallback_info: dict) -> (dict, Optional[str]): # Modified return type hints
    """Extracts metadata (duration, w, h) and thumbnail using ffmpeg."""
    metadata = {'duration': 0, 'width': 0, 'height': 0}
    thumb_path = None

    try:
        LOGGER.debug(f"Probing metadata for: {file_path}")
        probe = await asyncio.to_thread(ffmpeg.probe, file_path) # Run blocking probe in thread

        format_info = probe.get('format', {})
        stream_info = next((s for s in probe.get('streams', []) if s.get('codec_type') == media_type), None)

        # Duration
        duration_str = format_info.get('duration', stream_info.get('duration') if stream_info else None)
        if duration_str: metadata['duration'] = int(float(duration_str))

        # Dimensions (Video only)
        if media_type == 'video' and stream_info:
            metadata['width'] = int(stream_info.get('width', 0))
            metadata['height'] = int(stream_info.get('height', 0))

            # Thumbnail Generation
            if metadata['duration'] > 0:
                 thumb_path = f"{os.path.splitext(file_path)[0]}_thumb.jpg"
                 ss_time = metadata['duration'] * 0.1 if metadata['duration'] > 1 else 0.1
                 try:
                     LOGGER.debug(f"Generating thumbnail for {file_path} at {ss_time:.2f}s")
                     process = (
                         ffmpeg
                         .input(file_path, ss=ss_time)
                         .output(thumb_path, vframes=1, loglevel="error")
                         .overwrite_output()
                         .run_async(pipe_stdout=True, pipe_stderr=True) # Run async
                     )
                     _out, err = await process.communicate() # Wait for completion
                     if process.returncode != 0:
                          LOGGER.warning(f"ffmpeg thumbnail failed for {file_path}: {err.decode()}")
                          thumb_path = None
                     elif not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                          LOGGER.warning(f"ffmpeg thumbnail generated empty file for {file_path}")
                          thumb_path = None
                     else:
                          LOGGER.debug(f"Thumbnail generated: {thumb_path}")
                 except ffmpeg.Error as e:
                     LOGGER.warning(f"ffmpeg error generating thumbnail: {e.stderr.decode()}")
                     thumb_path = None
                 except Exception as e:
                     LOGGER.warning(f"Error generating thumbnail: {e}")
                     thumb_path = None

    except ImportError:
        LOGGER.warning("ffmpeg-python not installed. Metadata extraction/thumbnails disabled.")
    except ffmpeg.Error as e:
        LOGGER.warning(f"ffprobe failed for {file_path}: {e.stderr.decode()}")
    except Exception as e:
        LOGGER.error(f"Error extracting metadata for {file_path}: {e}", exc_info=True)

    # --- Fallback Metadata ---
    if metadata['duration'] == 0 and fallback_info.get('duration'):
        metadata['duration'] = int(float(fallback_info['duration']))
    if media_type == 'video':
        if metadata['width'] == 0 and fallback_info.get('width'): metadata['width'] = int(fallback_info['width'])
        if metadata['height'] == 0 and fallback_info.get('height'): metadata['height'] = int(fallback_info['height'])
        # Fallback thumbnail URL
        if not thumb_path and fallback_info.get('thumbnail'):
            thumb_path = fallback_info.get('thumbnail') # Use URL
            LOGGER.debug("Using fallback thumbnail URL.")

    return metadata, thumb_path

async def upload_file_to_telegram(client: Client, session_data: dict, status_message: Message, file_path: str, file_index: int, total_files: int) -> bool:
    """Uploads a single file to Telegram, handling progress and errors."""
    user_id = session_data.get('user_id')
    chat_id = session_data.get('chat_id')
    media_type = session_data.get('media_type')
    fallback_info = session_data.get('info_dict', {})
    reply_to_id = session_data.get('original_message_id')
    base_file_name = os.path.basename(file_path)

    LOGGER.info(f"Starting upload for user {user_id}: {base_file_name} ({file_index}/{total_files})")

    # Check size limit
    file_size = os.path.getsize(file_path)
    if file_size > MAX_TG_UPLOAD_SIZE:
        LOGGER.warning(f"File exceeds 2GB limit: {base_file_name} ({format_bytes(file_size)})")
        await client.send_message(chat_id, f"⚠️ حجم الملف `{base_file_name}` ({format_bytes(file_size)}) يتجاوز حد تيليجرام (2GB). لا يمكن رفعه.", reply_to_message_id=reply_to_id)
        return False # Indicate failure but allow process to continue

    # Extract Metadata and Thumbnail
    metadata, thumb_path = await extract_metadata_and_thumb(file_path, media_type, fallback_info)

    # Prepare Caption
    title = session_data.get('title', 'محتوى يوتيوب')
    pl_part = f"\nالجزء {file_index}/{total_files}" if total_files > 1 else ""
    caption = f"**{title}{pl_part}**\n\n"
    caption += f"تم التحميل بواسطة @{client.me.username}"
    caption = caption[:1020] # Limit caption length

    # Progress Args
    file_info = {'name': base_file_name, 'index': file_index, 'total': total_files}
    progress_args = (client, status_message, session_data, file_info)

    upload_success = False
    for attempt in range(2): # Allow one retry on generic error
        try:
            if media_type == 'video':
                await client.send_video(
                    chat_id=chat_id, video=file_path, caption=caption,
                    duration=metadata['duration'], width=metadata['width'], height=metadata['height'],
                    thumb=thumb_path, supports_streaming=True,
                    progress=upload_progress_hook, progress_args=progress_args,
                    reply_to_message_id=reply_to_id
                )
            elif media_type == 'audio':
                 performer = fallback_info.get('channel') or fallback_info.get('uploader', 'Unknown')
                 audio_title = os.path.splitext(base_file_name)[0]
                 await client.send_audio(
                     chat_id=chat_id, audio=file_path, caption=caption,
                     title=audio_title[:60], performer=performer[:60],
                     duration=metadata['duration'], thumb=thumb_path,
                     progress=upload_progress_hook, progress_args=progress_args,
                     reply_to_message_id=reply_to_id
                 )
            upload_success = True
            LOGGER.info(f"Upload successful for {base_file_name}")
            break # Exit retry loop on success

        except FloodWait as fw:
            LOGGER.warning(f"FloodWait for {fw.value}s during upload of {base_file_name}. Waiting...")
            await asyncio.sleep(fw.value + 2)
            # Retry is handled by the loop structure
        except Exception as e:
            LOGGER.error(f"Upload attempt {attempt+1} failed for {base_file_name}: {e}", exc_info=True)
            if attempt == 0:
                await asyncio.sleep(3) # Wait before retry
            else: # Last attempt failed
                 # Try sending as document as a last resort
                 LOGGER.warning(f"Falling back to sending as document: {base_file_name}")
                 try:
                     await client.send_document(
                         chat_id=chat_id, document=file_path, caption=caption,
                         thumb=thumb_path, force_document=True,
                         progress=upload_progress_hook, progress_args=progress_args,
                         reply_to_message_id=reply_to_id
                     )
                     upload_success = True # Consider document send a success
                     LOGGER.info(f"Sent as document successfully: {base_file_name}")
                 except Exception as doc_e:
                     LOGGER.error(f"Failed to send {base_file_name} as document: {doc_e}", exc_info=True)

    # Cleanup local file and thumb (always attempt)
    try:
        if os.path.exists(file_path): os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path) and not thumb_path.startswith('http'):
            os.remove(thumb_path)
    except OSError as e:
        LOGGER.warning(f"Error during file cleanup for {base_file_name}: {e}")

    return upload_success

# --- 5. Pyrogram Bot Setup and Handlers ---

# Initialize the bot client
app = Client(
    "URL_Uploader_Bot_Session", # Use a session name
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command(["start", "help"]) & filters.private)
async def start_handler(client: Client, message: Message):
    """Handles /start and /help commands."""
    LOGGER.info(f"User {message.from_user.id} started the bot.")
    await message.reply_text(
        "أهلاً بك! 👋\n"
        "أرسل رابط فيديو أو قائمة تشغيل يوتيوب لتحميله.\n\n"
        "استخدم الأمر /help لعرض التعليمات.",
        quote=True,
        disable_web_page_preview=True
    )

@app.on_message(filters.command("ping") & filters.private)
async def ping_handler(client: Client, message: Message):
    """Simple ping command for testing responsiveness."""
    LOGGER.info(f"Received /ping from user {message.from_user.id}")
    start_time = time.time()
    reply = await message.reply_text("Pong!", quote=True)
    end_time = time.time()
    await reply.edit_text(f"Pong! `{(end_time - start_time) * 1000:.2f} ms`")

# Regex for YouTube URLs
YOUTUBE_URL_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?(?:m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)/'
    r'(?:watch\?v=|embed/|v/|shorts/|playlist\?list=|live/|attribution_link\?a=)?'
    r'([\w-]{11,})(?:\S+)?'
)

@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "ping"]))
async def url_handler(client: Client, message: Message):
    """Handles incoming text messages containing YouTube URLs."""
    user_id = message.from_user.id
    url = message.text.strip()
    match = YOUTUBE_URL_REGEX.match(url)

    if not match:
        LOGGER.debug(f"Ignoring non-URL message from user {user_id}")
        # Optionally reply for non-URL messages if desired
        # await message.reply_text("يرجى إرسال رابط يوتيوب صالح.", quote=True)
        return

    LOGGER.info(f"Received URL from user {user_id}: {url.split('&')[0]}") # Log cleaned URL

    # Clear previous session if exists
    if user_id in user_sessions:
         LOGGER.warning(f"User {user_id} started a new request while previous session existed. Cleaning old one.")
         await cleanup_session(user_id) # Silently clean old session

    status_message = await message.reply_text("🔍 جاري جلب معلومات الرابط...", quote=True)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Fetch info
    info_dict = await get_youtube_info(url)
    await client.send_chat_action(message.chat.id, ChatAction.CANCEL)

    # Handle info fetching errors
    if 'error' in info_dict:
        await status_message.edit_text(f"❌ خطأ: {info_dict['error']}")
        return

    # Create initial selection
    caption, markup = create_media_type_selection(info_dict)
    await status_message.edit_text(caption, reply_markup=markup)

    # Store session data
    session_data = {
        'user_id': user_id,
        'chat_id': message.chat.id,
        'status_message_id': status_message.id,
        'original_message_id': message.id, # ID of the user's message with the link
        'url': url,
        'info_dict': info_dict,
        'title': info_dict.get('title', 'محتوى يوتيوب'),
        'media_type': None, # To be set by user
        'format_selector': None, # To be set
        'last_interaction_time': time.time(),
        'base_caption': caption.split('\n\n🔧')[0] # Store the info part of the caption
    }
    user_sessions[user_id] = session_data
    LOGGER.debug(f"Session created for user {user_id}")


@app.on_callback_query()
async def callback_query_handler(client: Client, callback_query: CallbackQuery):
    """Handles button presses."""
    user_id = callback_query.from_user.id
    data = callback_query.data
    message = callback_query.message

    # Check if session exists and is valid
    session_data = user_sessions.get(user_id)
    if not session_data or session_data.get('status_message_id') != message.id:
        await callback_query.answer("انتهت صلاحية هذه الخيارات أو تم بدء عملية أخرى.", show_alert=True)
        try: await message.edit_reply_markup(reply_markup=None) # Try remove buttons
        except: pass
        return

    # Update last interaction time
    session_data['last_interaction_time'] = time.time()
    await callback_query.answer() # Acknowledge the button press immediately

    # --- Handle Callbacks ---

    if data == "cancel_session":
        LOGGER.info(f"Session cancelled by user {user_id}")
        await cleanup_session(user_id, message, "❌ تم إلغاء العملية.")
        return

    elif data == "back_to_type":
        LOGGER.debug(f"User {user_id} going back to type selection.")
        caption, markup = create_media_type_selection(session_data['info_dict'])
        await edit_status_message(client, session_data, caption, markup)
        return

    elif data.startswith("type_"):
        media_type = data.split("_")[1] # audio or video
        session_data['media_type'] = media_type
        LOGGER.info(f"User {user_id} selected type: {media_type}")
        text, markup = create_format_selection(session_data['info_dict'], media_type)
        if markup:
            await edit_status_message(client, session_data, text, markup)
        else:
            await edit_status_message(client, session_data, f"⚠️ {text}", None) # Show error if no formats
            await cleanup_session(user_id) # Clean session if no formats found
        return

    elif data.startswith("format_"):
        format_selector, selected_media_type = get_format_selector(data)
        if not format_selector or not selected_media_type:
             LOGGER.warning(f"Invalid format callback data from user {user_id}: {data}")
             await edit_status_message(client, session_data, "حدث خطأ في تحديد الصيغة.", None)
             await cleanup_session(user_id)
             return

        # Ensure media type matches (should always unless logic error)
        if selected_media_type != session_data.get('media_type'):
             LOGGER.error(f"Mismatch between selected format media type ({selected_media_type}) and session media type ({session_data.get('media_type')}) for user {user_id}")
             await edit_status_message(client, session_data, "خطأ داخلي: عدم تطابق نوع الوسائط.", None)
             await cleanup_session(user_id)
             return

        session_data['format_selector'] = format_selector
        LOGGER.info(f"User {user_id} selected format. Selector: '{format_selector}'. Starting download...")

        # Update status message before starting download
        await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n🚀 جارٍ التحضير للتحميل...", None)

        # --- Download ---
        # Run blocking download in a separate thread
        downloaded_files, error_msg = await asyncio.to_thread(
            do_youtube_download,
            session_data['url'],
            format_selector,
            selected_media_type,
            session_data,
            message # Pass the message object for the hook wrapper
        )

        # Handle download errors
        if error_msg:
            LOGGER.error(f"Download failed for user {user_id}: {error_msg}")
            await edit_status_message(client, session_data, f"❌ فشل التحميل:\n`{error_msg}`", None)
            await cleanup_session(user_id)
            return
        if not downloaded_files:
            LOGGER.error(f"Download returned no files and no error for user {user_id}.")
            await edit_status_message(client, session_data, "❌ فشل التحميل ولم يتم العثور على ملفات.", None)
            await cleanup_session(user_id)
            return

        # --- Upload ---
        LOGGER.info(f"Download complete for user {user_id}. Found {len(downloaded_files)} file(s). Starting upload...")
        session_data['base_caption'] = f"✅ {session_data.get('title', 'اكتمل التحميل')}" # Update base caption for upload phase

        num_files = len(downloaded_files)
        upload_success_count = 0
        upload_errors = []

        for i, file_path in enumerate(downloaded_files):
            success = await upload_file_to_telegram(
                client, session_data, message, file_path, i + 1, num_files
            )
            if success:
                upload_success_count += 1
            else:
                 upload_errors.append(os.path.basename(file_path)) # Record name of failed file
            # Small delay between uploads in playlist
            if i < num_files - 1: await asyncio.sleep(1)

        # --- Final Status ---
        final_text = ""
        if upload_success_count == num_files:
            final_text = f"✅ تم رفع جميع الملفات ({num_files}) بنجاح!"
            LOGGER.info(f"All files uploaded successfully for user {user_id}.")
        elif upload_success_count > 0:
            final_text = f"⚠️ اكتملت العملية مع {num_files - upload_success_count} أخطاء. تم رفع {upload_success_count} ملف بنجاح.\nالملفات التي فشلت: {', '.join(upload_errors)}"
            LOGGER.warning(f"Upload finished with errors for user {user_id}. Success: {upload_success_count}/{num_files}")
        else:
            final_text = f"❌ فشل رفع جميع الملفات ({num_files})."
            LOGGER.error(f"All uploads failed for user {user_id}.")

        # Try editing status, fallback to sending new message
        if not await edit_status_message(client, session_data, final_text, None):
             try:
                 await client.send_message(session_data['chat_id'], final_text, reply_to_message_id=session_data['original_message_id'])
             except Exception as send_err:
                  LOGGER.error(f"Failed to send final status message for user {user_id}: {send_err}")

        # Delete status message after a delay (optional)
        # await asyncio.sleep(15)
        # try: await message.delete()
        # except: pass

        # Clean up the session
        await cleanup_session(user_id)


# --- 6. Bot Execution ---

if __name__ == "__main__":
    LOGGER.info("Starting URL Uploader Bot...")
    try:
        # Add any pre-run checks if needed
        app.run()
        # Code here runs after bot stops gracefully
        LOGGER.info("Bot stopped gracefully.")
    except Exception as e:
        LOGGER.critical(f"Bot stopped due to a critical error: {e}", exc_info=True)
    finally:
        LOGGER.info("Performing final cleanup...")
        # Clean download folder on exit (optional, be careful)
        # for f in os.listdir(DOWNLOAD_FOLDER):
        #     try: os.remove(os.path.join(DOWNLOAD_FOLDER, f))
        #     except OSError: pass
        print("تم إيقاف البوت.")
