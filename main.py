import os
import re
import yt_dlp
import ffmpeg  # For metadata and thumbnails
import asyncio
import math
import time
import logging
import http.cookiejar
from io import StringIO
from datetime import datetime
from typing import Optional, List, Dict, Any # Import Dict and Any for type hinting
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("yt_dlp").setLevel(logging.WARNING) # Reduce yt-dlp verbosity too

# Environment Variables
API_ID_STR = os.environ.get("API_ID", "") # استبدل بالقيم الخاصة بك إذا لم تكن في البيئة
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# YouTube Cookies Content (Keep as multiline string)
YTUB_COOKIES_CONTENT = """
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

# Validate Essential Config
if not all([API_ID_STR, API_HASH, BOT_TOKEN]):
    LOGGER.critical("FATAL ERROR: API_ID, API_HASH, or BOT_TOKEN is missing!")
    exit(1)
try:
    API_ID = int(API_ID_STR)
except ValueError:
    LOGGER.critical("FATAL ERROR: API_ID must be an integer!")
    exit(1)

# Constants
DOWNLOAD_FOLDER = "./downloads/"
MAX_TG_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2GB limit for Telegram
# SESSION_TIMEOUT = 1800 # Timeout for inactive sessions (can be implemented later)

# Global Session Dictionary
user_sessions: Dict[int, Dict[str, Any]] = {}

# Create Download Folder
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    LOGGER.info(f"Created download folder: {DOWNLOAD_FOLDER}")

# --- 2. Utility Functions ---

# [!] تم إزالة دالة load_cookies() المنفصلة. سيتم التحميل مباشرة في الدوال التي تحتاجها.

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
                if period_value > 0:
                    strings.append(f"{period_value} {period_name}")
        if not strings:
            return "أقل من ثانية" if seconds < 1 else "0 ثوان"
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

async def cleanup_session(user_id, message: Optional[Message] = None, text="انتهت صلاحية الجلسة أو تم إلغاؤها."):
    """Removes user session and optionally edits the status message."""
    session_data = user_sessions.pop(user_id, None) # Use pop to get and remove
    if session_data:
        LOGGER.info(f"Session cleaned for user {user_id}")
        if message:
            # Check if the message to edit is the one stored in the session
            session_message_id = session_data.get('status_message_id')
            if session_message_id == message.id:
                try:
                    await message.edit_text(text, reply_markup=None)
                except (MessageIdInvalid, MessageNotModified):
                    pass
                except Exception as e:
                    LOGGER.warning(f"Error editing message during session cleanup for user {user_id}: {e}")
        # Clean download files potentially associated (more robust needed for shared folder)
        # For now, we clean files after upload attempt in the main flow

async def edit_status_message(client: Client, session_data: dict, text: str, reply_markup=None):
    """Safely edits the status message associated with a session."""
    message_id = session_data.get('status_message_id')
    chat_id = session_data.get('chat_id')
    if not message_id or not chat_id:
        LOGGER.warning("Attempted to edit status message but ID or Chat ID is missing.")
        return False # Indicate failure
    try:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return True
    except MessageNotModified:
        return True # No change needed, but operationally successful
    except MessageIdInvalid:
        LOGGER.warning(f"Message {message_id} is invalid or deleted. Cannot edit.")
        session_data['status_message_id'] = None # Stop trying to edit
        return False
    except FloodWait as fw:
        LOGGER.warning(f"FloodWait for {fw.value}s while editing status message.")
        await asyncio.sleep(fw.value + 1)
        # Retry after wait - recursive call might be dangerous, let's return False
        return False # Let the caller decide if retry is needed
    except Exception as e:
        LOGGER.error(f"Failed to edit status message {message_id}: {e}", exc_info=True)
        return False

# --- 3. YouTube Interaction Functions ---

async def get_youtube_info(url: str) -> dict:
    """Fetches video info using yt-dlp. Returns info dict or {'error': msg}."""
    # --- تحميل الكوكيز مباشرة هنا ---
    cookie_jar = None
    if YTUB_COOKIES_CONTENT and YTUB_COOKIES_CONTENT.strip():
        try:
            temp_cookie_jar = http.cookiejar.MozillaCookieJar()
            # استخدم StringIO لتحميل الكوكيز من النص
            temp_cookie_jar.load(StringIO(YTUB_COOKIES_CONTENT), ignore_discard=True, ignore_expires=True)
            cookie_jar = temp_cookie_jar # قم بتعيين cookie_jar فقط إذا نجح التحميل
            LOGGER.debug("Cookies loaded successfully from variable for info fetching.")
        except Exception as e:
            # استخدم repr(e) للحصول على تفاصيل أكثر عن الخطأ
            LOGGER.warning(f"Error loading cookies from variable for info fetching: {repr(e)}. Proceeding without cookies.")
            cookie_jar = None # تأكد من أنها None في حالة الفشل
    else:
        LOGGER.debug("YTUB_COOKIES_CONTENT is empty or missing. Proceeding without cookies.")
    # --- نهاية تحميل الكوكيز ---

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'retries': 3,
        'extract_flat': 'discard_in_playlist', # More efficient for playlist info
        'dump_single_json': True, # Get JSON output directly
        'cookiejar': cookie_jar, # استخدم كائن cookie_jar المحمّل
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    }
    # إزالة مفتاح cookiejar إذا كانت قيمته None
    if ydl_opts['cookiejar'] is None:
        del ydl_opts['cookiejar']
        LOGGER.debug("Cookies are not being used for info fetching as they were not loaded or empty.")

    LOGGER.info(f"Fetching info for URL: {url}")
    try:
        # يجب تشغيل yt-dlp في thread منفصل لأنه عملية I/O ثقيلة (شبكة)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            LOGGER.info(f"Info fetched successfully for {url.split('&')[0]}")
            return info_dict
    except yt_dlp.utils.DownloadError as e:
        LOGGER.warning(f"yt-dlp info extraction failed: {e}")
        error_str = str(e).lower()
        if "video unavailable" in error_str: return {"error": "الفيديو غير متاح."}
        if "private video" in error_str: return {"error": "هذا الفيديو خاص."}
        if "confirm your age" in error_str: return {"error": "هذا المحتوى يتطلب تسجيل الدخول وتأكيد العمر (قد تحتاج إلى تحديث الكوكيز)."}
        if "premiere" in error_str: return {"error": "هذا الفيديو عرض أول ولم يبدأ بعد."}
        if "is live" in error_str: return {"error": "البث المباشر غير مدعوم حاليًا للتحميل."}
        if "http error 403" in error_str: return {"error": "خطأ 403: الوصول مرفوض (قد يكون مقيدًا جغرافيًا أو يتطلب كوكيز صالحة)."}
        if "http error 404" in error_str: return {"error": "خطأ 404: الفيديو غير موجود."}
        if "invalid url" in error_str: return {"error": "الرابط غير صالح أو غير مدعوم."}
        if "unable to download webpage" in error_str: return {"error": "تعذر الوصول إلى الرابط. تحقق من الاتصال أو الرابط."}
        # خطأ عام أكثر تفصيلاً
        detailed_error = getattr(e, 'msg', str(e)) # محاولة الحصول على رسالة خطأ أكثر تفصيلاً
        return {"error": f"فشل جلب المعلومات: {detailed_error[:200]}"}
    except Exception as e:
        LOGGER.error(f"General exception during info fetching: {e}", exc_info=True)
        return {"error": f"خطأ غير متوقع في جلب المعلومات: {repr(e)}"}

async def download_progress_hook_async(d: dict, client: Client, session_data: dict):
    """Async progress hook to update Telegram status message during download."""
    user_id = session_data.get('user_id')
    if not user_id: return

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
                speed_str = d.get('_speed_str', "N/A").strip()
                eta_str = d.get('_eta_str', "N/A").strip()
                filename = d.get('info_dict', {}).get('title', os.path.basename(d.get('filename', '')))[:50]
                pl_info = f" (مقطع {d.get('playlist_index')}/{d.get('playlist_count')})" if d.get('playlist_index') else ""

                text = (
                    f"{session_data.get('base_caption', '...')}\n\n"
                    f"**⏳ جاري التحميل{pl_info}:**\n"
                    f"`{filename}...`\n"
                    f"📦 {progress_bar_generator(percentage)} ({percentage * 100:.1f}%)\n"
                    f"💾 {format_bytes(downloaded_bytes)} / {format_bytes(total_bytes)}\n"
                    f"🚀 السرعة: {speed_str} | ⏳ المتبقي: {eta_str}"
                )

        elif d['status'] == 'finished':
            is_last = not d.get('playlist_index') or (d.get('playlist_index') == d.get('playlist_count'))
            if is_last:
                text = f"{session_data.get('base_caption', '...')}\n\n✅ اكتمل التحميل. جاري المعالجة والرفع..."
                session_data['base_caption'] = f"✅ {session_data.get('title', 'اكتمل التحميل')}"
            else:
                LOGGER.info(f"Playlist item {d.get('playlist_index')}/{d.get('playlist_count')} finished for user {user_id}.")
                return

        elif d['status'] == 'error':
            LOGGER.error(f"yt-dlp hook reported error during download for user {user_id}: {d.get('_error_cause', 'Unknown Error')}")
            return # Error handled by main download function return

        if text:
            # We need the client object here
            await edit_status_message(client, session_data, text)

    except Exception as e:
        LOGGER.error(f"Error in download progress hook for user {user_id}: {e}", exc_info=True)

# Wrapper for yt-dlp hook
def download_progress_hook_wrapper(d: dict):
    """Wrapper to run the async hook in the event loop."""
    session_data = d.get('session_data')
    client = d.get('client_instance') # Pass the client instance
    if session_data and client:
        try:
            loop = asyncio.get_running_loop() # Use get_running_loop
            asyncio.ensure_future(download_progress_hook_async(d, client, session_data), loop=loop)
        except RuntimeError:
            # Fallback if no loop (less likely in async context)
            LOGGER.warning("No running event loop found for download progress hook.")
            # asyncio.run(download_progress_hook_async(d, client, session_data)) # Avoid asyncio.run inside async code
    else:
        LOGGER.warning("Session data or client instance missing in download progress hook wrapper.")


def do_youtube_download(client: Client, url: str, format_selector: str, media_type: str, session_data: dict) -> (Optional[List[str]], Optional[str]):
    """
    Performs the download using yt-dlp in a blocking manner (intended to be run in a thread).
    Returns (list_of_file_paths, None) on success, or (None, error_message) on failure.
    Requires client instance for the progress hook.
    """
    user_id = session_data.get('user_id', 'UnknownUser')
    LOGGER.info(f"Starting download for user {user_id}, type: {media_type}, format: '{format_selector}'")

    # --- تحميل الكوكيز مباشرة هنا ---
    cookie_jar = None
    if YTUB_COOKIES_CONTENT and YTUB_COOKIES_CONTENT.strip():
        try:
            temp_cookie_jar = http.cookiejar.MozillaCookieJar()
            temp_cookie_jar.load(StringIO(YTUB_COOKIES_CONTENT), ignore_discard=True, ignore_expires=True)
            cookie_jar = temp_cookie_jar
            LOGGER.debug("Cookies loaded successfully from variable for download.")
        except Exception as e:
            LOGGER.warning(f"Error loading cookies from variable for download: {repr(e)}. Proceeding without cookies.")
            cookie_jar = None
    else:
        LOGGER.debug("YTUB_COOKIES_CONTENT is empty or missing. Proceeding without cookies for download.")
    # --- نهاية تحميل الكوكيز ---

    base_title = re.sub(r'[\\/*?:"<>|]', "_", session_data.get('title', 'youtube_dl'))[:80] # Sanitize more strictly and shorten
    # Use timestamp and random element for more uniqueness, especially for playlists
    timestamp = int(time.time())
    random_part = os.urandom(3).hex() # Add randomness
    output_template_base = os.path.join(DOWNLOAD_FOLDER, f"{user_id}_{timestamp}_{random_part}_{base_title}")

    final_expected_ext = 'mp3' if media_type == 'audio' else 'mp4'
    output_template = f'{output_template_base}_%(playlist_index)s.%(ext)s' if 'playlist' in url else f'{output_template_base}.%(ext)s'

    postprocessors = []
    if media_type == 'audio':
        # Request mp3 directly if possible, otherwise let ffmpeg handle it
        if 'bestaudio[ext=mp3]' not in format_selector and format_selector != 'bestaudio/best':
             format_selector += "/bestaudio[ext=m4a]/bestaudio" # Add fallbacks for audio
        output_template = os.path.splitext(output_template)[0] + '.%(ext)s' # Let PP determine ext
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', # Adjust quality as needed
        })
        # Ensure metadata is embedded
        postprocessors.append({'key': 'EmbedMetadata'})
        # Embed thumbnail if downloading audio from video
        if session_data.get('info_dict', {}).get('thumbnail'):
             postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})

    elif media_type == 'video':
        # Embed metadata and potentially subs if needed
        postprocessors.append({'key': 'EmbedMetadata'})
        postprocessors.append({
             'key': 'FFmpegMetadata',
             'add_metadata': True,
        })
        # Embed thumbnail for video as well
        if session_data.get('info_dict', {}).get('thumbnail'):
             postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
        # Ensure mp4 container if merging
        ydl_opts_merge = {'merge_output_format': 'mp4'}


    ydl_opts = {
        'format': format_selector,
        'outtmpl': output_template,
        'progress_hooks': [download_progress_hook_wrapper],
        'postprocessors': postprocessors,
        'nocheckcertificate': True,
        'prefer_ffmpeg': True, # Crucial: use ffmpeg when available
        'retries': 3,
        'fragment_retries': 3,
        'http_chunk_size': 10 * 1024 * 1024, # 10MB chunks
        'cookiejar': cookie_jar,
        'verbose': False,
        'quiet': True, # Set quiet to True for progress hooks to avoid extra console spam
        'ignoreerrors': True, # Continue playlist on error
        'writethumbnail': media_type == 'audio', # Write thumb for audio PP
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        },
        # Pass necessary data to the hook wrapper
        'session_data': session_data,
        'client_instance': client, # Pass client object
    }
    # Add merge options only for video
    if media_type == 'video':
         ydl_opts.update(ydl_opts_merge)

    if ydl_opts['cookiejar'] is None:
        del ydl_opts['cookiejar']

    downloaded_files = []
    final_error_message = None
    processed_files_info = [] # Store info about processed files

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Log options without sensitive data like cookies or session objects
            log_opts = {k: v for k, v in ydl_opts.items() if k not in ['cookiejar', 'session_data', 'client_instance', 'http_headers']}
            LOGGER.debug(f"Running yt-dlp for user {user_id} with opts: {log_opts}")
            info_dict = ydl.extract_info(url, download=True) # Blocking call
            LOGGER.info(f"yt-dlp process finished for user {user_id}")

            # --- Locate downloaded file(s) more reliably ---
            # yt-dlp provides 'requested_downloads' after processing
            processed_files_info = info_dict.get('requested_downloads', [])

            if not processed_files_info:
                 # Fallback for single files if 'requested_downloads' is missing
                 if 'entries' not in info_dict and info_dict.get('filepath'):
                     if os.path.exists(info_dict['filepath']):
                          processed_files_info.append({'filepath': info_dict['filepath']})
                     else:
                          # Try constructing final path if PP was used
                          expected_path_base = os.path.splitext(ydl.prepare_filename(info_dict))[0]
                          expected_path = f"{expected_path_base}.{final_expected_ext}"
                          if os.path.exists(expected_path):
                              processed_files_info.append({'filepath': expected_path})

                 # Fallback for playlists (less reliable)
                 elif 'entries' in info_dict:
                      LOGGER.warning(f"No 'requested_downloads' found for playlist for user {user_id}. Trying fallback.")
                      entries = info_dict.get('entries', [])
                      if entries:
                           for i, entry in enumerate(entries):
                               if entry: # Skip None entries on error
                                   try:
                                       # Construct expected path based on template
                                       # Need to handle potential PP extension change
                                       entry_filename_base = ydl.prepare_filename(entry).replace('.%(ext)s', '') # Remove placeholder if present
                                       potential_path_pp = f"{entry_filename_base}.{final_expected_ext}"
                                       potential_path_orig = f"{entry_filename_base}.{entry.get('ext')}"

                                       if os.path.exists(potential_path_pp):
                                            processed_files_info.append({'filepath': potential_path_pp})
                                            LOGGER.debug(f"Found playlist file via fallback PP path: {potential_path_pp}")
                                       elif os.path.exists(potential_path_orig):
                                            processed_files_info.append({'filepath': potential_path_orig})
                                            LOGGER.debug(f"Found playlist file via fallback original path: {potential_path_orig}")
                                       else:
                                            LOGGER.warning(f"Fallback couldn't find file for playlist entry index {i}: {entry.get('title', 'N/A')}")
                                   except Exception as fallback_err:
                                       LOGGER.error(f"Error during playlist fallback file finding for index {i}: {fallback_err}")


            # Extract file paths from the processed info
            for dl_info in processed_files_info:
                filepath = dl_info.get('filepath')
                if filepath and os.path.exists(filepath):
                    downloaded_files.append(filepath)
                    LOGGER.debug(f"Successfully located downloaded/processed file for user {user_id}: {filepath}")
                else:
                    LOGGER.warning(f"File path missing or file does not exist in requested_downloads for user {user_id}: {filepath}")


    except yt_dlp.utils.DownloadError as e:
        LOGGER.error(f"yt-dlp download failed for user {user_id}: {e}", exc_info=False) # Keep exc_info False for less noise
        error_str = str(e).lower()
        if "video unavailable" in error_str: final_error_message = "الفيديو غير متاح."
        elif "private video" in error_str: final_error_message = "هذا الفيديو خاص (تحقق من الكوكيز)."
        elif "confirm your age" in error_str: final_error_message = "المحتوى يتطلب تأكيد العمر (تحقق من الكوكيز)."
        elif "http error 403" in error_str: final_error_message = "خطأ 403: الوصول مرفوض (قد يكون مقيدًا أو يتطلب كوكيز صالحة)."
        elif "http error 429" in error_str: final_error_message = "خطأ 429: تم إرسال طلبات كثيرة جدًا (حاول لاحقًا)."
        elif "unable to download webpage" in error_str: final_error_message = "تعذر الوصول إلى الرابط للتحميل."
        elif "ffmpeg not found" in error_str:
             final_error_message = "خطأ: أداة ffmpeg غير موجودة وهي مطلوبة لهذه الصيغة/الجودة."
             # Add instruction about ffmpeg
             final_error_message += "\nيرجى تثبيت ffmpeg: https://github.com/yt-dlp/yt-dlp#dependencies"
        else:
             detailed_error = getattr(e, 'msg', str(e))
             final_error_message = f"فشل التحميل: {detailed_error[:200]}"
    except Exception as e:
        LOGGER.error(f"General exception during download execution for user {user_id}: {e}", exc_info=True)
        final_error_message = f"حدث خطأ عام غير متوقع أثناء التحميل: {repr(e)}"

    # Final check
    valid_files = [f for f in downloaded_files if os.path.exists(f)]
    if not valid_files and not final_error_message:
        LOGGER.error(f"Download process finished for user {user_id} but no valid files found and no specific error reported by yt-dlp.")
        final_error_message = "فشل التحميل لسبب غير معروف ولم يتم العثور على ملفات صالحة."

    if final_error_message:
        # Clean up any potentially partially downloaded files based on template
        try:
            for item in os.listdir(DOWNLOAD_FOLDER):
                 if item.startswith(os.path.basename(output_template_base)):
                     os.remove(os.path.join(DOWNLOAD_FOLDER, item))
                     LOGGER.debug(f"Cleaned up potential partial file: {item}")
        except OSError as clean_err:
            LOGGER.warning(f"Error cleaning up partial files for user {user_id}: {clean_err}")
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
                  (isinstance(info_dict.get('entries'), list) and info_dict.get('entries') is not None) # Check entries is not None
    item_count = len(info_dict['entries']) if is_playlist and info_dict.get('entries') else 1

    caption = f"**{title}**\n\n"
    if channel: caption += f"📺 **القناة:** `{channel}`\n" # Use code formatting for channel
    if is_playlist:
        caption += f"🔢 **عدد المقاطع:** {item_count}\n"
    elif duration != "N/A":
        caption += f"⏱️ **المدة:** {duration}\n"

    caption = caption.strip() # Remove trailing newline
    caption = caption[:800] + f"\n\n🔧 **اختر نوع التحميل المطلوب:**" # Ensure separator is added

    buttons = [
        [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
        [InlineKeyboardButton("إلغاء ❌", callback_data="cancel_session")]
    ]
    markup = InlineKeyboardMarkup(buttons)
    return caption, markup

def create_format_selection(info_dict: dict, media_type: str) -> (Optional[str], Optional[InlineKeyboardMarkup]):
    """Creates text and buttons for selecting download format/quality."""
    formats = info_dict.get('formats', [])
    if not formats: return "لم يتم العثور على صيغ متاحة.", None

    buttons = []
    text = ""
    found_formats_count = 0 # Count actual options added

    if media_type == 'video':
        text = "🎬 اختر جودة الفيديو المطلوبة:"
        # Filter for formats with both video and audio, preferring mp4
        video_formats = [
            f for f in formats
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none'
            and f.get('ext') == 'mp4' # Prefer mp4 directly
            and f.get('height') is not None # Ensure height is present
        ]
        # Fallback if no direct mp4 found
        if not video_formats:
             video_formats = [
                 f for f in formats
                 if f.get('vcodec') != 'none'
                 and f.get('height') is not None
             ]

        # Group by height and select best (often first listed by yt-dlp for a resolution)
        grouped_formats: Dict[int, Dict[str, Any]] = {}
        for f in sorted(video_formats, key=lambda x: (x.get('height', 0), x.get('fps', 0), x.get('tbr', 0)), reverse=True):
             h = f.get('height')
             if h and h not in grouped_formats:
                 grouped_formats[h] = f

        # Create buttons for common resolutions
        resolutions_to_show = [1080, 720, 480, 360] # Show in descending order
        for res in resolutions_to_show:
             fmt = grouped_formats.get(res)
             # Also check slightly lower resolutions if exact not found (e.g., find 480 if 540 exists)
             if not fmt:
                  closest_res = max([h for h in grouped_formats if h <= res], default=None)
                  if closest_res:
                      fmt = grouped_formats.get(closest_res)

             if fmt:
                 # Display format details
                 height = fmt.get('height')
                 ext = fmt.get('ext', '?')
                 vcodec = fmt.get('vcodec', '').split('.')[0] # Cleaner codec name
                 size_approx = format_bytes(fmt.get('filesize') or fmt.get('filesize_approx'))
                 label = f"{height}p ({ext}, {vcodec})"
                 if size_approx != "N/A": label += f" - {size_approx}"
                 # Use specific format ID for more reliable selection later
                 format_id = fmt.get('format_id')
                 if format_id:
                     buttons.append([InlineKeyboardButton(label[:60], callback_data=f"format_video_{format_id}")])
                     found_formats_count += 1
                 # Remove found format to avoid duplicates if checking lower resolutions
                 if res in grouped_formats: del grouped_formats[res]
                 if fmt.get('height') in grouped_formats: del grouped_formats[fmt.get('height')]


        # Add a 'best' option if nothing else found or as fallback
        if not buttons:
            buttons.append([InlineKeyboardButton("أفضل جودة متاحة (تلقائي)", callback_data="format_video_best")])
            found_formats_count += 1


    elif media_type == 'audio':
        text = "🔉 اختر جودة الصوت المطلوبة:"
        # Prioritize audio-only formats
        audio_only = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('abr') is not None]
        # Fallback: include combined formats if no audio-only or limited options
        combined_audio = [f for f in formats if f.get('acodec') != 'none' and f.get('abr') is not None]

        # Sort by bitrate (handle NoneType using the fix)
        # [!] FIX: Handle None in abr sorting
        key_func = lambda x: float(x.get('abr') or 0)
        sorted_audio = sorted(audio_only, key=key_func, reverse=True)
        if len(sorted_audio) < 3: # Add combined if few audio-only found
             sorted_audio.extend(sorted(combined_audio, key=key_func, reverse=True))

        # Deduplicate based on label and add buttons
        added_labels = set()
        buttons.append([InlineKeyboardButton("أفضل جودة صوت 🏆 (MP3)", callback_data="format_audio_bestmp3")]) # Explicit MP3 best
        found_formats_count += 1

        count = 0
        for f in sorted_audio:
            if count >= 4: break # Limit to 4 specific + best
            fid = f.get('format_id')
            if not fid: continue

            abr = f.get('abr')
            codec = f.get('acodec', '').replace('mp4a.40.2', 'aac').split('.')[0]
            ext = f.get('ext')
            size_approx = format_bytes(f.get('filesize') or f.get('filesize_approx'))

            label_parts = []
            if abr: label_parts.append(f"~{abr:.0f}k")
            label_parts.append(codec)
            label_parts.append(f"({ext})")
            if size_approx != "N/A": label_parts.append(f"- {size_approx}")
            label = " ".join(label_parts)

            if label not in added_labels:
                buttons.append([InlineKeyboardButton(label[:60], callback_data=f"format_audio_{fid}")])
                added_labels.add(label)
                count += 1
                found_formats_count += 1


    if found_formats_count == 0: # Check if any buttons were actually added
        return f"لم يتم العثور على صيغ مناسبة قابلة للعرض لـ {media_type}.", None

    buttons.append([InlineKeyboardButton("رجوع ↩️", callback_data="back_to_type"), InlineKeyboardButton("إلغاء ❌", callback_data="cancel_session")])
    markup = InlineKeyboardMarkup(buttons)
    return text, markup

def get_format_selector(callback_data: str, info_dict: dict) -> (Optional[str], Optional[str]):
    """
    Determines the yt-dlp format selector string based on callback data.
    Returns (format_selector, media_type) or (None, None).
    Needs info_dict to construct selectors involving bestaudio/video.
    """
    parts = callback_data.split('_', 2)
    if len(parts) < 3: return None, None # Invalid format

    f_type, media, selection = parts # e.g., format, video, 137 OR format, audio, bestmp3

    if media == 'video':
        if selection == 'best':
            # Best video MP4 + best audio M4A, with fallbacks
             return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best", "video"
        else:
            # Selection is likely a format_id (e.g., 137)
            # We need to combine it with the best audio stream
            # Find best audio format ID (prefer m4a)
            best_audio_id = None
            formats = info_dict.get('formats', [])
            audio_formats = sorted(
                [f for f in formats if f.get('acodec') != 'none' and f.get('ext') == 'm4a'],
                key=lambda x: float(x.get('abr') or 0), reverse=True
            )
            if not audio_formats: # Fallback to any audio
                 audio_formats = sorted(
                     [f for f in formats if f.get('acodec') != 'none'],
                     key=lambda x: float(x.get('abr') or 0), reverse=True
                 )

            if audio_formats:
                 best_audio_id = audio_formats[0].get('format_id')

            if best_audio_id:
                 # Construct selector: specific video + best audio / specific video (if it has audio)
                 return f"{selection}+{best_audio_id}/{selection}", "video"
            else:
                 # Fallback if no separate audio found (unlikely for YouTube)
                 return selection, "video"

    elif media == 'audio':
        if selection == "bestmp3":
            # Prefer best audio-only MP3, fallback to best audio-only, fallback to best overall audio
            return "bestaudio[ext=mp3]/bestaudio", "audio" # Rely on PP to convert to mp3
        else:
            # Selection is a format_id
            return selection, "audio"

    return None, None # Unknown type

async def upload_progress_hook(current, total, client: Client, session_data: dict, file_info: dict):
    """Async progress hook for Telegram uploads."""
    user_id = session_data.get('user_id')
    if not user_id: return

    now = time.time()
    last_update = session_data.get('last_upload_update_time', 0)
    # Update slightly more frequently during upload
    if now - last_update < 1.0: return
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
            f" {progress_bar_generator(percentage)} ({percentage * 100:.1f}%)\n"
            f" {format_bytes(current)} / {format_bytes(total)}"
        )
        # Pass client directly
        await edit_status_message(client, session_data, text)

    except Exception as e:
        LOGGER.error(f"Error in upload progress hook for user {user_id}: {e}", exc_info=True)

async def extract_metadata_and_thumb(file_path: str, media_type: str, fallback_info: dict) -> (dict, Optional[str]):
    """Extracts metadata (duration, w, h) and thumbnail using ffmpeg or ffprobe."""
    metadata = {'duration': 0, 'width': 0, 'height': 0}
    thumb_path = None
    ffmpeg_found = True # Assume found initially

    try:
        LOGGER.debug(f"Probing metadata for: {file_path}")
        # Use asyncio.to_thread for blocking ffprobe call
        probe_task = asyncio.to_thread(ffmpeg.probe, file_path)
        probe = await asyncio.wait_for(probe_task, timeout=15) # Add timeout

        format_info = probe.get('format', {})
        # Find the relevant stream (video or audio)
        stream_info = next((s for s in probe.get('streams', []) if s.get('codec_type') == media_type),
                           probe.get('streams', [{}])[0]) # Fallback to first stream if type match fails

        # Duration (more reliable from format if available)
        duration_str = format_info.get('duration', stream_info.get('duration'))
        if duration_str and duration_str != 'N/A':
            try: metadata['duration'] = int(float(duration_str))
            except (ValueError, TypeError): pass

        # Dimensions (Video only)
        if media_type == 'video' and stream_info:
            metadata['width'] = int(stream_info.get('width', 0))
            metadata['height'] = int(stream_info.get('height', 0))

        # Thumbnail Generation (Video only, using ffmpeg command)
        if media_type == 'video' and metadata['duration'] > 0:
            thumb_path = f"{os.path.splitext(file_path)[0]}_thumb.jpg"
            # Capture frame slightly into the video
            ss_time = min(metadata['duration'] * 0.1, 5.0) if metadata['duration'] > 1 else 0.1 # Max 5s in

            try:
                LOGGER.debug(f"Attempting to generate thumbnail for {file_path} at {ss_time:.2f}s")
                # Use asyncio subprocess for ffmpeg command
                process = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-ss', str(ss_time), '-i', file_path,
                    '-vframes', '1', '-n', '-loglevel', 'error', # -n prevents overwrite prompt
                    thumb_path,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20) # Timeout for ffmpeg

                if process.returncode != 0:
                    LOGGER.warning(f"ffmpeg thumbnail generation failed for {file_path}. Return code: {process.returncode}. Stderr: {stderr.decode(errors='ignore')}")
                    thumb_path = None
                elif not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                    LOGGER.warning(f"ffmpeg thumbnail generated an empty or non-existent file: {thumb_path}")
                    thumb_path = None
                else:
                    LOGGER.debug(f"Thumbnail generated successfully: {thumb_path}")

            except FileNotFoundError:
                 LOGGER.warning("ffmpeg command not found. Cannot generate thumbnails.")
                 thumb_path = None
                 ffmpeg_found = False # Mark ffmpeg as not found
            except asyncio.TimeoutError:
                 LOGGER.warning(f"ffmpeg thumbnail generation timed out for {file_path}")
                 thumb_path = None
            except Exception as thumb_err:
                 LOGGER.error(f"Error during ffmpeg thumbnail generation: {thumb_err}", exc_info=True)
                 thumb_path = None

    except FileNotFoundError:
         LOGGER.warning("ffmpeg/ffprobe not found. Metadata extraction/thumbnails disabled.")
         ffmpeg_found = False
    except asyncio.TimeoutError:
         LOGGER.warning(f"ffprobe timed out for {file_path}")
    except (ImportError, NameError): # Handle if ffmpeg-python is not installed
        LOGGER.warning("ffmpeg-python library not installed. Install with 'pip install ffmpeg-python'.")
        ffmpeg_found = False
    except ffmpeg.Error as e: # Catch ffmpeg-python specific errors
        LOGGER.warning(f"ffprobe failed for {file_path}: {e.stderr.decode(errors='ignore') if e.stderr else e.stdout.decode(errors='ignore')}")
    except Exception as e:
        LOGGER.error(f"General error extracting metadata for {file_path}: {e}", exc_info=True)

    # --- Fallback Metadata from yt-dlp info_dict ---
    if metadata['duration'] == 0 and fallback_info.get('duration'):
        metadata['duration'] = int(float(fallback_info['duration']))
    if media_type == 'video':
        if metadata['width'] == 0 and fallback_info.get('width'):
            metadata['width'] = int(fallback_info['width'])
        if metadata['height'] == 0 and fallback_info.get('height'):
            metadata['height'] = int(fallback_info['height'])

    # Fallback thumbnail URL (only if ffmpeg failed or wasn't used)
    # Check if thumb was generated by postprocessor first
    potential_pp_thumb = os.path.splitext(file_path)[0] + ".jpg" # yt-dlp might make this
    if os.path.exists(potential_pp_thumb):
         thumb_path = potential_pp_thumb
         LOGGER.debug(f"Using thumbnail potentially generated by yt-dlp postprocessor: {thumb_path}")
    elif not thumb_path and fallback_info.get('thumbnail'):
        thumb_path = fallback_info.get('thumbnail') # Use URL as last resort
        LOGGER.debug("Using fallback thumbnail URL from yt-dlp info.")

    # Clean up non-URL thumb path if it doesn't exist
    if thumb_path and not thumb_path.startswith('http') and not os.path.exists(thumb_path):
         thumb_path = None

    # If ffmpeg wasn't found, use yt-dlp duration/dims as primary
    if not ffmpeg_found:
         metadata['duration'] = int(float(fallback_info.get('duration', 0)))
         if media_type == 'video':
              metadata['width'] = int(fallback_info.get('width', 0))
              metadata['height'] = int(fallback_info.get('height', 0))
         LOGGER.debug("Using yt-dlp metadata due to missing ffmpeg/ffprobe.")


    return metadata, thumb_path

async def upload_file_to_telegram(client: Client, session_data: dict, file_path: str, file_index: int, total_files: int) -> bool:
    """Uploads a single file to Telegram, handling progress and errors."""
    user_id = session_data.get('user_id')
    chat_id = session_data.get('chat_id')
    media_type = session_data.get('media_type')
    # Use the full info_dict for fallback
    fallback_info = session_data.get('info_dict', {})
    # If playlist, try to get specific entry info
    if total_files > 1 and 'entries' in fallback_info and fallback_info['entries'] and len(fallback_info['entries']) >= file_index:
        entry_info = fallback_info['entries'][file_index - 1]
        if entry_info: # Use entry info if available
            fallback_info = entry_info

    reply_to_id = session_data.get('original_message_id')
    base_file_name = os.path.basename(file_path)

    LOGGER.info(f"Starting upload for user {user_id}: {base_file_name} ({file_index}/{total_files})")

    # Check size limit
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_TG_UPLOAD_SIZE:
            LOGGER.warning(f"File exceeds 2GB limit for user {user_id}: {base_file_name} ({format_bytes(file_size)})")
            await client.send_message(
                chat_id,
                f"⚠️ حجم الملف `{base_file_name}` ({format_bytes(file_size)}) يتجاوز حد تيليجرام (2GB). لا يمكن رفعه.",
                reply_to_message_id=reply_to_id
            )
            return False # Indicate failure but allow process to continue for other files
    except OSError as e:
        LOGGER.error(f"Could not get size for file {file_path}: {e}")
        await client.send_message(
            chat_id,
            f"⚠️ تعذر الحصول على حجم الملف `{base_file_name}`. تخطي الرفع.",
            reply_to_message_id=reply_to_id
        )
        return False

    # Extract Metadata and Thumbnail
    metadata, thumb_path = await extract_metadata_and_thumb(file_path, media_type, fallback_info)

    # Prepare Caption
    title = fallback_info.get('title', session_data.get('title', 'محتوى يوتيوب')) # Use entry title if available
    pl_part = f"\nالجزء {file_index}/{total_files}" if total_files > 1 else ""
    caption = f"**{title}{pl_part}**\n\n"
    # Add duration if available
    if metadata.get('duration', 0) > 0:
         caption += f"⏱️ المدة: {td_format(metadata['duration'])}\n"
    # Add channel if available
    channel = fallback_info.get('channel') or fallback_info.get('uploader')
    if channel:
         caption += f"📺 القناة: `{channel}`\n"

    caption += f"\nتم التحميل بواسطة @{client.me.username}"
    caption = caption[:1020] # Limit caption length (Telegram limit is 1024)

    # Progress Args
    file_info = {'name': base_file_name, 'index': file_index, 'total': total_files}
    # Pass client and session_data directly to the hook
    progress_args = (client, session_data, file_info)

    upload_success = False
    last_exception = None

    # Send Chat Action
    action = ChatAction.UPLOAD_VIDEO if media_type == 'video' else ChatAction.UPLOAD_AUDIO
    try:
        await client.send_chat_action(chat_id, action)
    except Exception as ca_e:
        LOGGER.warning(f"Could not send chat action {action}: {ca_e}")


    for attempt in range(2): # Allow one retry on generic error
        try:
            if media_type == 'video':
                await client.send_video(
                    chat_id=chat_id, video=file_path, caption=caption,
                    duration=metadata.get('duration', 0),
                    width=metadata.get('width', 0),
                    height=metadata.get('height', 0),
                    thumb=thumb_path, # Pyrogram handles URL or path
                    supports_streaming=True,
                    progress=upload_progress_hook, progress_args=progress_args,
                    reply_to_message_id=reply_to_id,
                    parse_mode=ParseMode.MARKDOWN # Ensure Markdown is enabled for caption
                )
            elif media_type == 'audio':
                performer = fallback_info.get('channel') or fallback_info.get('uploader', 'Unknown Artist')
                audio_title = fallback_info.get('title', os.path.splitext(base_file_name)[0]) # Use YT title if available
                await client.send_audio(
                    chat_id=chat_id, audio=file_path, caption=caption,
                    title=audio_title[:60], # Limit title length
                    performer=performer[:60], # Limit performer length
                    duration=metadata.get('duration', 0),
                    thumb=thumb_path,
                    progress=upload_progress_hook, progress_args=progress_args,
                    reply_to_message_id=reply_to_id,
                    parse_mode=ParseMode.MARKDOWN
                )
            upload_success = True
            LOGGER.info(f"Upload successful for {base_file_name} (user {user_id})")
            break # Exit retry loop on success

        except FloodWait as fw:
            LOGGER.warning(f"FloodWait for {fw.value}s during upload of {base_file_name} (user {user_id}). Waiting...")
            await asyncio.sleep(fw.value + 2)
            last_exception = fw # Store exception to potentially report later
            # Retry is handled by the loop structure
        except Exception as e:
            last_exception = e # Store exception
            LOGGER.error(f"Upload attempt {attempt + 1} failed for {base_file_name} (user {user_id}): {e}", exc_info=True)
            if attempt == 0:
                await asyncio.sleep(3) # Wait briefly before retry
            else: # Last attempt failed
                # Try sending as document as a final resort for non-FloodWait errors
                if not isinstance(e, FloodWait):
                    LOGGER.warning(f"Falling back to sending as document for {base_file_name} (user {user_id})")
                    try:
                        # Need different progress args if needed for document
                        doc_progress_args = (client, session_data, {'name': f"[Doc] {base_file_name}", 'index': file_index, 'total': total_files})
                        await client.send_document(
                            chat_id=chat_id, document=file_path, caption=caption,
                            thumb=thumb_path, # Thumb might work for docs too
                            force_document=True,
                            progress=upload_progress_hook, progress_args=doc_progress_args,
                            reply_to_message_id=reply_to_id,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        upload_success = True # Consider document send a success
                        LOGGER.info(f"Sent as document successfully: {base_file_name} (user {user_id})")
                    except FloodWait as doc_fw:
                         LOGGER.warning(f"FloodWait for {doc_fw.value}s during document fallback upload (user {user_id}).")
                         await asyncio.sleep(doc_fw.value + 2)
                         # Don't retry document send, just report failure
                    except Exception as doc_e:
                        LOGGER.error(f"Failed to send {base_file_name} as document: {doc_e}", exc_info=True)
                        last_exception = doc_e # Update last exception


    # Cleanup local file and thumb (always attempt, even on failure)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            LOGGER.debug(f"Removed downloaded file: {file_path}")
        # Remove thumb only if it's a generated file path, not a URL
        if thumb_path and not thumb_path.startswith('http') and os.path.exists(thumb_path):
            os.remove(thumb_path)
            LOGGER.debug(f"Removed generated thumbnail: {thumb_path}")
    except OSError as e:
        LOGGER.warning(f"Error during file cleanup for {base_file_name} (user {user_id}): {e}")

    # Report specific error if upload ultimately failed
    if not upload_success and last_exception:
         error_type = type(last_exception).__name__
         error_details = str(last_exception)
         # Avoid overly long Telegram messages
         if len(error_details) > 200: error_details = error_details[:200] + "..."
         try:
             await client.send_message(
                 chat_id,
                 f"⚠️ فشل رفع الملف `{base_file_name}`.\nالخطأ: `{error_type}: {error_details}`",
                 reply_to_message_id=reply_to_id
             )
         except Exception as report_err:
             LOGGER.error(f"Failed to report upload error for {base_file_name}: {report_err}")


    return upload_success

# --- 5. Pyrogram Bot Setup and Handlers ---

# Initialize the bot client
app = Client(
    "URL_Uploader_Bot_Session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4 # Adjust worker count based on server resources
)

@app.on_message(filters.command(["start", "help"]) & filters.private)
async def start_handler(client: Client, message: Message):
    """Handles /start and /help commands."""
    LOGGER.info(f"User {message.from_user.id} ({message.from_user.username}) used /start or /help.")
    start_text = (
        "أهلاً بك! 👋\n"
        "أنا بوت تحميل من يوتيوب.\n\n"
        "**كيفية الاستخدام:**\n"
        "1.  أرسل رابط فيديو أو قائمة تشغيل يوتيوب.\n"
        "2.  اختر نوع التحميل (فيديو 🎬 أو صوت 🔉).\n"
        "3.  اختر الجودة المطلوبة.\n"
        "4.  انتظر حتى يتم التحميل والرفع.\n\n"
        "**ملاحظات:**\n"
        "- يتطلب البوت أداة `ffmpeg` للحصول على أفضل النتائج وتحويل الصوت إلى MP3. "
        "إذا واجهت مشاكل في جودة الصوت أو الفيديو، قد يكون السبب عدم تثبيت `ffmpeg`.\n"
        "- يتم حذف الملفات من الخادم مباشرة بعد الرفع.\n"
        "- يوجد حد لحجم الملفات في تيليجرام (2GB).\n\n"
        "للبدء، فقط أرسل الرابط!"
    )
    await message.reply_text(
        start_text,
        quote=True,
        disable_web_page_preview=True,
        reply_to_message_id=message.id # Reply to the command message
    )

@app.on_message(filters.command("ping") & filters.private)
async def ping_handler(client: Client, message: Message):
    """Simple ping command for testing responsiveness."""
    user_id = message.from_user.id
    LOGGER.info(f"Received /ping from user {user_id}")
    start_time = time.monotonic()
    reply = await message.reply_text("...", quote=True, reply_to_message_id=message.id)
    end_time = time.monotonic()
    await reply.edit_text(f"Pong! 🏓 `{(end_time - start_time) * 1000:.2f} ms`")

# Improved Regex for YouTube URLs (handles more variations)
YOUTUBE_URL_REGEX = re.compile(
    r'(?:https?://)?' # Optional scheme
    r'(?:www\.|m\.)?' # Optional www. or m. subdomain
    r'(?:youtube(?:-nocookie)?\.com|youtu\.be)' # Domain
    r'/(?:' # Non-capturing group for path variations
        r'watch\?v=|'
        r'embed/|'
        r'v/|'
        r'shorts/|'
        r'live/|'
        r'playlist\?list=|'
        r'channel/|'
        r'user/|'
        r'c/|'
        r'[@]?[a-zA-Z0-9_-]+/?(?:videos|streams|shorts)?/?|' # Handle channel names with @ or c/
        r'attribution_link\?.*v%3D' # Handle attribution links
    r')?' # End path variations group (optional)
    r'([\w-]{11})' # Capture Video ID (usually 11 characters)
    r'(?:\S+)?' # Allow other parameters without capturing
)
# Regex specifically for playlists
YOUTUBE_PLAYLIST_REGEX = re.compile(r'list=([\w-]+)')

@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "ping"]))
async def url_handler(client: Client, message: Message):
    """Handles incoming text messages containing YouTube URLs."""
    user_id = message.from_user.id
    url = message.text.strip()

    # Basic URL validation first
    if not url.startswith(('http://', 'https://')):
        # Allow youtube.com/youtu.be without scheme for convenience
        if url.startswith(('youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com')):
             url = "https://" + url
        else:
             await message.reply_text("يرجى إرسال رابط يبدأ بـ http أو https.", quote=True)
             return

    # Check if it looks like a valid YouTube link using regex
    match = YOUTUBE_URL_REGEX.search(url)
    playlist_match = YOUTUBE_PLAYLIST_REGEX.search(url)

    is_playlist_link = bool(playlist_match)
    is_video_link = bool(match)

    if not is_video_link and not is_playlist_link:
        LOGGER.debug(f"Ignoring non-YouTube URL message from user {user_id}")
        await message.reply_text("لم يتم التعرف على الرابط كرابط يوتيوب صالح.", quote=True)
        return

    # Prefer playlist ID if both video and list are present in URL
    effective_url = url # Use the full URL for yt-dlp initially
    log_url = url.split('&')[0] # Cleaner URL for logging

    LOGGER.info(f"Received URL from user {user_id} ({message.from_user.username}): {log_url}")

    # --- Session Management ---
    # Check for existing session
    if user_id in user_sessions:
        LOGGER.warning(f"User {user_id} has an existing session. Cleaning old one.")
        # Try to edit the old status message before cleaning
        old_session_data = user_sessions.get(user_id)
        if old_session_data:
             await edit_status_message(client, old_session_data, "تم بدء عملية جديدة. تم إلغاء العملية السابقة.", None)
        await cleanup_session(user_id) # Clean the session data

    # Send initial status message
    status_message = await message.reply_text("🔍 جاري جلب معلومات الرابط...", quote=True, reply_to_message_id=message.id)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Fetch info using the helper function
    info_dict = await get_youtube_info(effective_url)
    try:
        await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
    except: pass # Ignore if action already cancelled

    # Handle info fetching errors
    if 'error' in info_dict:
        error_text = f"❌ خطأ في جلب المعلومات:\n`{info_dict['error']}`"
        # Add hint about cookies for common errors
        if "403" in info_dict['error'] or "private" in info_dict['error'] or "age" in info_dict['error']:
             error_text += "\n\n(قد تحتاج إلى تحديث الكوكيز الخاصة بالبوت إذا كان المحتوى خاصًا أو يتطلب تسجيل دخول)"
        await status_message.edit_text(error_text)
        return

    # Create initial media type selection
    caption, markup = create_media_type_selection(info_dict)
    await edit_status_message(client, { "chat_id": message.chat.id, "status_message_id": status_message.id }, caption, markup)

    # Store session data
    session_data = {
        'user_id': user_id,
        'chat_id': message.chat.id,
        'status_message_id': status_message.id,
        'original_message_id': message.id,
        'url': effective_url, # Store the URL used for fetching
        'info_dict': info_dict, # Store fetched info
        'title': info_dict.get('title', 'محتوى يوتيوب'),
        'media_type': None,
        'format_selector': None,
        'last_interaction_time': time.time(),
        'base_caption': caption.split('\n\n🔧')[0].strip() # Store info part
    }
    user_sessions[user_id] = session_data
    LOGGER.debug(f"Session created for user {user_id}. Status message ID: {status_message.id}")


@app.on_callback_query()
async def callback_query_handler(client: Client, callback_query: CallbackQuery):
    """Handles button presses."""
    user_id = callback_query.from_user.id
    data = callback_query.data
    message = callback_query.message # The message with the buttons

    # Check if session exists and matches the message
    session_data = user_sessions.get(user_id)
    if not session_data or session_data.get('status_message_id') != message.id:
        await callback_query.answer("انتهت صلاحية هذه الخيارات أو تم بدء عملية أخرى.", show_alert=True)
        try:
            # Attempt to remove buttons from the expired message
            await message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass # Ignore if message is already gone or changed
        return

    # Update last interaction time to prevent premature cleanup (if timeout implemented)
    session_data['last_interaction_time'] = time.time()

    # Acknowledge the button press immediately
    try:
        await callback_query.answer()
    except Exception as ack_err:
         LOGGER.warning(f"Could not acknowledge callback query {callback_query.id}: {ack_err}")


    # --- Handle Callbacks ---

    if data == "cancel_session":
        LOGGER.info(f"Session cancelled by user {user_id}")
        # Pass the message object to edit it during cleanup
        await cleanup_session(user_id, message, "❌ تم إلغاء العملية.")
        return

    elif data == "back_to_type":
        LOGGER.debug(f"User {user_id} going back to type selection.")
        caption, markup = create_media_type_selection(session_data['info_dict'])
        await edit_status_message(client, session_data, caption, markup)
        return

    elif data.startswith("type_"):
        media_type = data.split("_")[1] # audio or video
        if media_type not in ['audio', 'video']:
             LOGGER.warning(f"Invalid media type '{media_type}' from callback for user {user_id}")
             return # Ignore invalid data

        session_data['media_type'] = media_type
        LOGGER.info(f"User {user_id} selected type: {media_type}")

        # Show placeholder message while generating formats
        await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n⏳ جاري البحث عن الجودات المتاحة لـ **{media_type}**...", None)

        text, markup = create_format_selection(session_data['info_dict'], media_type)
        if markup:
            await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n{text}", markup)
        else:
            # If no formats found, show error and clean up
            await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n⚠️ {text}", None)
            await asyncio.sleep(2) # Let user see the message
            await cleanup_session(user_id, message, f"لا توجد صيغ متاحة لـ {media_type}.")
        return

    elif data.startswith("format_"):
        format_selector, selected_media_type = get_format_selector(data, session_data['info_dict'])

        if not format_selector or not selected_media_type:
            LOGGER.warning(f"Invalid format callback data or failed selector generation from user {user_id}: {data}")
            await edit_status_message(client, session_data, "حدث خطأ في تحديد الصيغة المختارة.", None)
            await cleanup_session(user_id, message) # Clean up on error
            return

        # Ensure media type matches the session's selected type
        if selected_media_type != session_data.get('media_type'):
            LOGGER.error(f"Media type mismatch! Session: {session_data.get('media_type')}, Format CB: {selected_media_type}. User: {user_id}")
            await edit_status_message(client, session_data, "خطأ داخلي: عدم تطابق نوع الوسائط المختار.", None)
            await cleanup_session(user_id, message)
            return

        session_data['format_selector'] = format_selector
        LOGGER.info(f"User {user_id} selected format. Selector: '{format_selector}'. Media: {selected_media_type}. Starting download...")

        # --- Download Phase ---
        # Update status message before starting blocking download
        await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n🚀 جارٍ التحضير للتحميل بالصيغة المختارة...", None)

        # Run the blocking download function in a separate thread
        download_task = asyncio.to_thread(
            do_youtube_download,
            client, # Pass client instance needed for progress hook
            session_data['url'],
            format_selector,
            selected_media_type,
            session_data
        )
        # Wait for the download to complete
        downloaded_files, error_msg = await download_task

        # Handle download errors
        if error_msg:
            LOGGER.error(f"Download failed for user {user_id}: {error_msg}")
            await edit_status_message(client, session_data, f"❌ فشل التحميل:\n`{error_msg}`", None)
            await cleanup_session(user_id) # Clean session, message already edited
            return
        if not downloaded_files:
            LOGGER.error(f"Download returned no files and no error message for user {user_id}.")
            await edit_status_message(client, session_data, "❌ فشل التحميل ولم يتم العثور على ملفات صالحة.", None)
            await cleanup_session(user_id)
            return

        # --- Upload Phase ---
        LOGGER.info(f"Download complete for user {user_id}. Found {len(downloaded_files)} file(s). Starting upload...")
        # Update base caption for upload phase (already done in hook on finish)
        # session_data['base_caption'] = f"✅ {session_data.get('title', 'اكتمل التحميل')}"

        num_files = len(downloaded_files)
        upload_success_count = 0
        upload_errors = []

        # Update status before starting upload loop
        await edit_status_message(client, session_data, f"{session_data['base_caption']}\n\n⬆️ جاري تهيئة الرفع لـ {num_files} ملف...", None)

        for i, file_path in enumerate(downloaded_files):
            if not os.path.exists(file_path):
                 LOGGER.warning(f"File {file_path} disappeared before upload for user {user_id}. Skipping.")
                 upload_errors.append(f"{os.path.basename(file_path)} (ملف مفقود)")
                 continue

            # Pass client and session_data directly to upload function
            success = await upload_file_to_telegram(
                client, session_data, file_path, i + 1, num_files
            )
            if success:
                upload_success_count += 1
            else:
                # Error reporting is handled inside upload_file_to_telegram
                # We just need to know it failed for the final summary
                upload_errors.append(os.path.basename(file_path))

            # Small delay between uploads, especially in playlists
            if i < num_files - 1:
                await asyncio.sleep(2) # Increase delay slightly

        # --- Final Status Update ---
        final_text = ""
        log_level = logging.INFO
        delete_status_message = True # Delete status message on full success

        if upload_success_count == num_files:
            final_text = f"✅ تم رفع جميع الملفات ({num_files}) بنجاح!"
            log_level = logging.INFO
        elif upload_success_count > 0:
            failed_count = num_files - upload_success_count
            final_text = f"⚠️ اكتملت العملية مع {failed_count} أخطاء. تم رفع {upload_success_count} ملف بنجاح."
            # Don't list failed files here as they were reported individually
            # final_text += f"\nالملفات التي فشلت: {', '.join(upload_errors)}"
            log_level = logging.WARNING
            delete_status_message = False # Keep status message if errors occurred
        else:
            final_text = f"❌ فشل رفع جميع الملفات ({num_files})."
            log_level = logging.ERROR
            delete_status_message = False # Keep status message

        LOGGER.log(log_level, f"Upload process finished for user {user_id}. Success: {upload_success_count}/{num_files}")

        # Try editing the status message one last time
        # If successful and delete_status_message is True, delete it after a delay
        if await edit_status_message(client, session_data, final_text, None):
            if delete_status_message:
                 await asyncio.sleep(10) # Wait a bit for user to see
                 try:
                     await message.delete()
                     LOGGER.debug(f"Deleted final status message {message.id} for user {user_id}")
                 except Exception as del_err:
                     LOGGER.warning(f"Could not delete final status message {message.id}: {del_err}")
        else:
            # If editing failed, try sending a new message as fallback
            try:
                await client.send_message(session_data['chat_id'], final_text, reply_to_message_id=session_data['original_message_id'])
            except Exception as send_err:
                LOGGER.error(f"Failed to send final status message as fallback for user {user_id}: {send_err}")

        # Clean up the session regardless of upload success/failure
        await cleanup_session(user_id) # Use cleanup without message object now


# --- 6. Bot Execution ---

async def main():
    global app # Make app accessible if needed elsewhere, though handlers have client
    async with app:
        # Get bot info
        me = await app.get_me()
        LOGGER.info(f"Bot started as @{me.username} (ID: {me.id})")

        # Add any other startup tasks here
        # Example: Check ffmpeg availability
        try:
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                 LOGGER.info("ffmpeg found successfully.")
            else:
                 LOGGER.warning("ffmpeg check failed. Postprocessing and best quality might be affected.")
                 LOGGER.warning("Install ffmpeg for optimal performance: https://github.com/yt-dlp/yt-dlp#dependencies")
        except FileNotFoundError:
            LOGGER.warning("ffmpeg command not found. Postprocessing and best quality will be affected.")
            LOGGER.warning("Install ffmpeg for optimal performance: https://github.com/yt-dlp/yt-dlp#dependencies")
        except Exception as ffmpeg_check_err:
             LOGGER.error(f"Error checking ffmpeg version: {ffmpeg_check_err}")


        # Keep the bot running indefinitely (Pyrogram's run() handles this implicitly)
        # We use `async with app` which handles start/stop
        LOGGER.info("Bot is now running and waiting for messages...")
        # To keep running forever if not using `app.run()` directly
        await asyncio.Event().wait() # Keep running until stopped externally

if __name__ == "__main__":
    LOGGER.info("Starting URL Uploader Bot...")
    try:
        # Run the main async function
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("Bot stopping gracefully...")
    except Exception as e:
        LOGGER.critical(f"Bot stopped due to a critical error in main execution: {e}", exc_info=True)
    finally:
        LOGGER.info("Performing final cleanup...")
        # Optional: Clean download folder on exit (use with caution)
        # count = 0
        # for f in os.listdir(DOWNLOAD_FOLDER):
        #     try:
        #         os.remove(os.path.join(DOWNLOAD_FOLDER, f))
        #         count += 1
        #     except OSError as clean_e:
        #         LOGGER.warning(f"Could not remove file on exit: {f} - {clean_e}")
        # if count > 0: LOGGER.info(f"Cleaned {count} file(s) from download folder.")

        # Ensure all sessions are cleared (though cleanup should handle this)
        user_sessions.clear()
        LOGGER.info("User sessions cleared.")
        print("\nتم إيقاف البوت.")
