# قم بأضافة الكوكيز للتحميل
import os
import re
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified, MessageIdInvalid, FloodWait
import http.cookiejar
from io import StringIO
from pyrogram.enums import ChatAction
import asyncio
import math
# Removed glob as it's less reliable than yt-dlp's output finding
import time # Import time for throttling and unique filenames
# Import ffmpeg, but make its usage optional
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    print("WARN: ffmpeg-python not found. Metadata extraction and thumbnail generation will be limited.")

# --- بيانات البوت ---
# Ensure you have these environment variables set
API_ID = os.environ.get("API_ID",)
API_HASH = os.environ.get("API_HASH","")
BOT_TOKEN = os.environ.get("BOT_TOKEN","")

# --- Check if essential variables are set ---
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("خطأ: متغيرات البيئة API_ID, API_HASH, و BOT_TOKEN يجب تعيينها.")

# --- ملف الكوكيز ---
# Use the variable directly from the environment or the provided default
YTUB_COOKIES_CONTENT = os.environ.get("YTUB_COOKIES", """
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
""")

bot = Client(
    "URL_UPLOADER_BOT", # Changed name slightly to avoid potential conflicts
    api_id=int(API_ID), # Ensure API_ID is an integer
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- مجلد التحميل ---
DOWNLOAD_FOLDER = "./downloads/"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"DEBUG: Created download folder: {DOWNLOAD_FOLDER}")

# --- قاموس لتخزين بيانات التنزيل المؤقتة ---
download_sessions = {} # {user_id: {data}}

# --- دالة مساعد لتحميل الكوكيز ---
def load_cookies():
    """Loads cookies from the YTUB_COOKIES_CONTENT string."""
    cookie_jar = http.cookiejar.MozillaCookieJar()
    if YTUB_COOKIES_CONTENT and YTUB_COOKIES_CONTENT.strip():
        # Remove leading/trailing whitespace and ensure header is present
        cleaned_cookies = YTUB_COOKIES_CONTENT.strip()
        if not cleaned_cookies.startswith("# Netscape HTTP Cookie File"):
            cleaned_cookies = "# Netscape HTTP Cookie File\n" + cleaned_cookies

        try:
            # Use StringIO to treat the string as a file
            cookie_jar.load(StringIO(cleaned_cookies), ignore_discard=True, ignore_expires=True)
            print("DEBUG: Cookies loaded successfully from variable.")
            # Optional: Print loaded cookies for verification (remove in production)
            # for cookie in cookie_jar:
            #     print(f"DEBUG: Loaded Cookie: {cookie.name}={cookie.value}")
            return cookie_jar
        except Exception as e:
            print(f"ERROR: Failed to load cookies from variable: {e}. Proceeding without cookies.")
            return None
    else:
        print("DEBUG: YTUB_COOKIES_CONTENT is empty. Proceeding without cookies.")
        return None

# --- دالة تنسيق حجم الملف ---
def format_bytes(size):
    """Converts bytes to a human-readable format."""
    if size is None:
       return "N/A" # Return N/A if size is None
    try:
        size = float(size)
        if size == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        # Ensure index is within bounds, especially for very small or large numbers
        i = max(0, min(len(size_name) - 1, i))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return f"{s} {size_name[i]}"
    except (ValueError, TypeError, OverflowError):
        # Handle cases where size might not be a number or causes math errors
        return "N/A"

# --- دالة تنزيل الفيديو/قائمة التشغيل ---
def download_youtube_content(url, message, format_selector, user_id, media_type):
    """Downloads content using yt-dlp based on selected format."""
    print(f"DEBUG: Starting download for URL: {url}, format_selector: {format_selector}, type: {media_type}")
    # --- Get Initial Info for Title Sanitization ---
    sanitized_title = f"youtube_download_{user_id}_{int(time.time())}" # Default fallback
    final_title = 'محتوى يوتيوب'
    final_description = 'لا يوجد وصف'
    original_ext = 'mp4' # Default assumption

    try:
        pre_ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'extract_flat': 'discard_in_playlist', # Faster for playlist title
            'dump_single_json': True,
            'retries': 3 # Fewer retries for info fetch
        }
        cookie_jar_pre = load_cookies()
        if cookie_jar_pre:
            pre_ydl_opts['cookiejar'] = cookie_jar_pre

        with yt_dlp.YoutubeDL(pre_ydl_opts) as ydl_pre:
            info_pre = ydl_pre.extract_info(url, download=False)
            base_title = info_pre.get('title', f'youtube_{info_pre.get("id", "download")}')
            # More aggressive sanitization, replace invalid chars with underscore
            sanitized_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', base_title)[:100] # Limit length
            # Use the fetched title/desc if available
            final_title = info_pre.get('title', final_title)
            final_description = info_pre.get('description', final_description)
            original_ext = info_pre.get('ext', original_ext)
            print(f"DEBUG: Sanitized title base: {sanitized_title}")
    except Exception as e:
        print(f"DEBUG: Error fetching initial info for sanitization: {e}. Using default title.")
        # Fallback title already set

    # --- Prepare yt-dlp Options for Actual Download ---
    cookie_jar = load_cookies() # Load again for the actual download
    output_template_base = os.path.join(DOWNLOAD_FOLDER, sanitized_title)
    final_expected_ext = 'mp4' # Default expected extension for video after potential merge

    ydl_opts = {
        'progress_hooks': [lambda d: asyncio.run_coroutine_threadsafe(progress_hook(d, message, user_id), bot.loop).result()], # Run async hook in bot's loop
        'format': format_selector,
        'verbose': False, # Less verbose output unless debugging
        'quiet': True, # Quieter console output
        'retries': 10,
        'fragment_retries': 10,
        'http_chunk_size': 10 * 1024 * 1024, # 10MB chunks
        'nocheckcertificate': True,
        'prefer_ffmpeg': True, # Essential for merging/conversion
        'postprocessors': [],
        'outtmpl': f'{output_template_base}.%(ext)s', # Initial template
        'keepvideo': False, # Don't keep separate streams after merge
        'concurrent_fragment_downloads': 5, # Parallel fragment downloads
        'merge_output_format': 'mp4', # Merge separate video/audio into mp4
        'final_ext': 'mp4', # Hint for final extension for video
        'http_headers': { # Mimic browser headers
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8'
        }
    }
    if cookie_jar:
        ydl_opts['cookiejar'] = cookie_jar

    if media_type == 'audio':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # Convert to MP3
            'preferredquality': '192', # Standard MP3 quality
        })
        # IMPORTANT: Let FFmpegExtractAudio handle the final filename and extension
        ydl_opts['outtmpl'] = f'{output_template_base}.%(ext)s' # Let initial download happen
        # We will look for .mp3 after postprocessing
        final_expected_ext = 'mp3'
        # Remove merge format if only extracting audio
        ydl_opts.pop('merge_output_format', None)
        ydl_opts.pop('final_ext', None)
    else: # Video
        # Keep merge_output_format = 'mp4'
        final_expected_ext = 'mp4'

    # --- Execute Download ---
    downloaded_files = []
    error_message = None
    info_dict = None # To store the final info_dict
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"DEBUG: Running yt-dlp with options: {ydl_opts}")
            # This will download AND process
            info_dict = ydl.extract_info(url, download=True)
            print(f"DEBUG: yt-dlp finished execution.")

            # --- Locate Downloaded File(s) ---
            # Update title/description from the *final* info_dict after potential playlist processing
            if info_dict:
                final_title = info_dict.get('title', final_title)
                final_description = info_dict.get('description', final_description)

            is_playlist = 'entries' in info_dict and info_dict['entries'] is not None

            if is_playlist:
                print(f"DEBUG: Processing playlist results ({len(info_dict.get('entries', []))} entries)...")
                for entry in info_dict.get('entries', []):
                    if not entry: continue # Skip None entries if yt-dlp failed on one

                    # Path finding logic for playlist entries
                    entry_filepath = entry.get('filepath') # Path after all processing (yt-dlp >= 2023.06.22)
                    entry_requested_path = entry.get('_requested_filename') # Path before post-processing
                    entry_title_raw = entry.get('title', f'playlist_entry_{entry.get("id", "unknown")}')
                    entry_sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', entry_title_raw)[:100]
                    entry_base = os.path.join(DOWNLOAD_FOLDER, entry_sanitized)
                    entry_expected_final_path = f"{entry_base}.{final_expected_ext}"

                    found_path = None
                    # 1. Check final 'filepath' if available and exists
                    if entry_filepath and os.path.exists(entry_filepath):
                        found_path = entry_filepath
                        print(f"DEBUG: Found playlist file via 'filepath': {found_path}")
                    # 2. Check constructed path with expected final extension
                    elif os.path.exists(entry_expected_final_path):
                         found_path = entry_expected_final_path
                         print(f"DEBUG: Found playlist file via constructed path: {found_path}")
                    # 3. Check the path yt-dlp *requested* before post-processing (might exist if PP failed)
                    elif entry_requested_path and os.path.exists(entry_requested_path):
                         found_path = entry_requested_path
                         print(f"DEBUG: Found playlist file via '_requested_filename': {found_path}")
                    # 4. Fallback check common extensions for video/audio
                    else:
                         extensions_to_check = [final_expected_ext, 'mkv', 'webm'] if media_type == 'video' else [final_expected_ext, 'm4a', 'opus']
                         for ext_guess in extensions_to_check:
                             fallback_path = f"{entry_base}.{ext_guess}"
                             if os.path.exists(fallback_path):
                                 found_path = fallback_path
                                 print(f"DEBUG: Found playlist file via fallback '{ext_guess}': {found_path}")
                                 break
                    if found_path:
                         downloaded_files.append(found_path)
                    else:
                         print(f"WARN: Cannot find downloaded file for playlist entry: '{entry_title_raw}'. Expected base: {entry_base}, Ext: {final_expected_ext}")
                         print(f"  -> Checked: filepath='{entry_filepath}', expected='{entry_expected_final_path}', requested='{entry_requested_path}'")

            else: # Single video/audio
                print("DEBUG: Processing single item result...")
                filepath = info_dict.get('filepath') # Final path after processing
                requested_path = info_dict.get('_requested_filename') # Path before post-processing
                expected_final_path = f"{output_template_base}.{final_expected_ext}"

                found_path = None
                # 1. Check final 'filepath' if available and exists
                if filepath and os.path.exists(filepath):
                    found_path = filepath
                    print(f"DEBUG: Found single file via 'filepath': {found_path}")
                # 2. Check constructed path with expected final extension
                elif os.path.exists(expected_final_path):
                    found_path = expected_final_path
                    print(f"DEBUG: Found single file via constructed path: {found_path}")
                # 3. Check the path yt-dlp *requested* before post-processing
                elif requested_path and os.path.exists(requested_path):
                    found_path = requested_path
                    print(f"DEBUG: Found single file via '_requested_filename': {found_path}")
                # 4. Fallback check common extensions
                else:
                     extensions_to_check = [final_expected_ext, 'mkv', 'webm'] if media_type == 'video' else [final_expected_ext, 'm4a', 'opus']
                     for ext_guess in extensions_to_check:
                         fallback_path = f"{output_template_base}.{ext_guess}"
                         if os.path.exists(fallback_path):
                             found_path = fallback_path
                             print(f"DEBUG: Found single file via fallback '{ext_guess}': {found_path}")
                             break

                if found_path:
                    downloaded_files.append(found_path)
                else:
                    error_message = "لم يتم العثور على الملف النهائي بعد التنزيل والمعالجة."
                    print(f"ERROR: Could not find final file for '{final_title}'. Expected base: {output_template_base}, Ext: {final_expected_ext}")
                    print(f"  -> Checked: filepath='{filepath}', expected='{expected_final_path}', requested='{requested_path}'")


    except yt_dlp.utils.DownloadError as e:
        print(f"ERROR: yt-dlp download failed: {e}")
        error_str = str(e).lower() # Lowercase for easier checking
        # Provide more specific user-friendly messages
        if "unsupported url" in error_str: error_message = "الرابط غير مدعوم."
        elif "video unavailable" in error_str: error_message = "الفيديو غير متاح."
        elif "private video" in error_str: error_message = "هذا الفيديو خاص."
        elif "login required" in error_str or "confirm your age" in error_str: error_message = "هذا الفيديو يتطلب تسجيل الدخول أو تأكيد العمر (قد تحتاج لكوكيز صالحة)."
        elif "premiere" in error_str: error_message = "الفيديو عرض أول ولم يبدأ بعد."
        elif "is live" in error_str: error_message = "البث المباشر غير مدعوم حاليًا للتحميل."
        elif "http error 429" in error_str or "too many requests" in error_str: error_message = "خطأ 429: تم حظر IP مؤقتًا بسبب كثرة الطلبات. حاول لاحقًا."
        elif "http error 403" in error_str or "forbidden" in error_str: error_message = "خطأ 403: الوصول مرفوض (قد يكون مقيدًا أو يتطلب كوكيز أحدث)."
        elif "http error 404" in error_str: error_message = "خطأ 404: الملف أو الفيديو غير موجود."
        elif "postprocessing:" in error_str:
             # Extract postprocessing error if possible
             pp_error_match = re.search(r"error:\s*(.*?)(?:$|\n)", error_str)
             pp_error = pp_error_match.group(1).strip() if pp_error_match else "فشل في المعالجة"
             error_message = f"خطأ في المعالجة: {pp_error}"
             if "ffmpeg" in error_str and "not found" in error_str: error_message = "خطأ في المعالجة: لم يتم العثور على FFmpeg."

        elif "unable to download webpage" in error_str or "network error" in error_str or "resolve host" in error_str:
            error_message = "خطأ في الشبكة أو تعذر الوصول للرابط."
        else:
            # Try to extract a cleaner error message
            match = re.search(r'ERROR: (.*?)(?:;|$)', str(e), re.IGNORECASE | re.DOTALL)
            extracted_err = match.group(1).strip() if match else str(e)
            error_message = f"فشل التحميل: {extracted_err[:200]}" # Limit length
            error_message = error_message.replace(DOWNLOAD_FOLDER, '') # Obscure local path

    except Exception as e:
        # Catch potential errors from the file finding logic or other issues
        print(f"ERROR: General download exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        error_message = f"حدث خطأ عام غير متوقع: {e}"

    # Final check: Ensure all reported files actually exist
    final_files = [f for f in downloaded_files if os.path.exists(f)]
    if len(final_files) != len(downloaded_files):
        missing_count = len(downloaded_files) - len(final_files)
        print(f"WARN: {missing_count} file(s) reported by yt-dlp do not exist on disk.")
        # Optionally add to error message if some files are missing after a supposed success
        if not error_message and missing_count > 0:
             error_message = f"تم تحميل {len(final_files)}/{len(downloaded_files)} ملف بنجاح، لكن بعض الملفات مفقودة."

    # If no files were found and no specific error was set, set a generic error
    if not final_files and not error_message:
        error_message = "فشل التحميل لسبب غير معروف ولم يتم العثور على ملفات."
        print("ERROR: Download process finished but no files were found and no specific error recorded.")

    print(f"DEBUG: Returning files: {final_files}, error: {error_message}, title: {final_title}")
    return final_files, error_message, final_title, final_description

# --- دالة عرض التقدم (Download Only) ---
# Needs to be async as it's called via run_coroutine_threadsafe
async def progress_hook(d, message, user_id):
    """Updates the message with download progress."""
    # Check if the session is still active for this user
    session_data = download_sessions.get(user_id)
    status_message_id = session_data.get('status_message_id') if session_data else None
    # Exit if session is gone, message ID is unknown, or hook is for a different message
    if not session_data or not status_message_id or message.id != status_message_id:
        # print(f"DEBUG: Progress hook skipped for user {user_id} - session/message mismatch.")
        return

    now = time.time()
    last_update = session_data.get('last_download_update_time', 0)
    # Allow 'finished' and 'error' states to bypass throttling for final updates
    if d['status'] not in ['finished', 'error'] and (now - last_update < 1.5) : # 1.5 second throttle
        return
    session_data['last_download_update_time'] = now

    try:
        current_text = ""
        markup = None # Keep markup=None unless we are showing the final download message

        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')

            if total_bytes and downloaded_bytes:
                percentage = downloaded_bytes / total_bytes
                speed_str = d.get('speed_str', d.get('_speed_str', "N/A")) # yt-dlp uses 'speed_str'
                eta_str = d.get('eta_str', d.get('_eta_str', "N/A"))       # yt-dlp uses 'eta_str'
                total_size_str = format_bytes(total_bytes)
                downloaded_size_str = format_bytes(downloaded_bytes)
                progress_bar_str = progress_bar_generator(percentage)

                # Try to get filename from info_dict if available, otherwise from hook dict
                filename_info = d.get('info_dict', {}).get('title', os.path.basename(d.get('filename', '')))[:50]
                if not filename_info: filename_info = os.path.basename(d.get('tmpfilename', 'download'))[:50]

                # Playlist info
                playlist_index = d.get('playlist_index')
                playlist_count = d.get('playlist_count')
                playlist_info = f" (مقطع {playlist_index}/{playlist_count})" if playlist_index and playlist_count else ""

                current_text = (
                    f"**⏳ جاري التحميل{playlist_info}:**\n"
                    f"`{filename_info}...`\n"
                    f"📦 {progress_bar_str} ({percentage*100:.1f}%)\n"
                    f"💾 {downloaded_size_str} / {total_size_str}\n"
                    f"🚀 السرعة: {speed_str} | ⏳ المتبقي: {eta_str}"
                )

        elif d['status'] == 'finished':
            filename = d.get('filename')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            print(f"DEBUG: Download finished for: {filename} (Size: {format_bytes(total_bytes)})")

            # Check if it's the last item in a playlist or a single video
            is_last_or_single = False
            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            if not playlist_index or playlist_index == playlist_count:
                 is_last_or_single = True

            if is_last_or_single:
                 # This is the final download completion signal
                 current_text = "✅ اكتمل التحميل. جاري المعالجة والرفع..."
                 session_data['initial_text'] = "✅ اكتمل التحميل." # Update base text for upload stage
                 markup = None # Remove buttons now (already done in format_callback, but belt-and-suspenders)
            else:
                 # For intermediate playlist items, just log and don't edit the main message
                 filename_info = d.get('info_dict', {}).get('title', os.path.basename(filename))[:50]
                 print(f"DEBUG: Playlist item {playlist_index}/{playlist_count} download finished: {filename_info}")
                 return # Don't edit the main status message for intermediate finishes

        elif d['status'] == 'error':
            # yt-dlp already logs errors, we handle the main error in download_youtube_content
            print(f"ERROR: yt-dlp hook reported an error during download process: {d.get('error', 'Unknown hook error')}")
            # We won't update the message here, the main function will handle the final error message
            return # Let the main function report the final error

        # Edit the message only if text is generated and message ID is valid
        if current_text and status_message_id:
             await bot.edit_message_text(
                  chat_id=message.chat.id,
                  message_id=status_message_id,
                  # Prepend the initial text only for the 'downloading' status update
                  text=f"{session_data.get('initial_text', '')}\n\n{current_text}" if d['status'] == 'downloading' else current_text,
                  reply_markup=markup # Should be None for downloading/finished
             )

    except MessageNotModified:
        # print("DEBUG: Message not modified (progress hook)")
        pass
    except FloodWait as fw:
        print(f"FloodWait in progress_hook: Waiting {fw.value} seconds...")
        await asyncio.sleep(fw.value + 1)
    except MessageIdInvalid:
        print(f"WARN: Message ID {status_message_id} invalid in progress_hook. Clearing from session.")
        if user_id in download_sessions:
            download_sessions[user_id]['status_message_id'] = None # Stop further edits
    except Exception as e:
        print(f"ERROR in progress_hook: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        if user_id in download_sessions:
            download_sessions[user_id]['status_message_id'] = None # Stop further edits


# --- دالة إنشاء شريط التقدم المرئي ---
def progress_bar_generator(percentage, bar_length=15): # Keep it relatively short
    """Generates a textual progress bar."""
    try:
        percentage = float(percentage)
        # Ensure percentage is between 0 and 1
        percentage = max(0.0, min(1.0, percentage))
        completed_blocks = int(round(bar_length * percentage))
        remaining_blocks = bar_length - completed_blocks
        return '█' * completed_blocks + '░' * remaining_blocks
    except (ValueError, TypeError):
        return '░' * bar_length # Return empty bar on error

# --- معالج أوامر البدء ---
@bot.on_message(filters.command(["start", "help"]) & filters.private)
async def start_command(client, message):
    """Handles the /start and /help commands."""
    await message.reply_text(
        "أهلاً بك! أنا بوت تحميل فيديوهات وقوائم تشغيل يوتيوب.\n"
        "أرسل لي رابط فيديو يوتيوب أو قائمة تشغيل وسأقوم بتحميلها وإرسالها لك.\n\n"
        "**طريقة الاستخدام:**\n"
        "1. أرسل رابط يوتيوب (فيديو، قائمة تشغيل، أو Short) في هذه الدردشة.\n"
        "2. اختر نوع التحميل (فيديو أو صوت).\n"
        "3. اختر الجودة المطلوبة من القائمة (ضعيف، متوسط، عالي للفيديو / أو جودة صوت محددة).\n\n"
        "**الصيغ المدعومة:**\n"
        "- الفيديو: MP4 (عادةً ما يتم الدمج في هذا التنسيق).\n"
        "- الصوت: MP3 (يتم التحويل لهذا التنسيق).\n\n"
        "**ملاحظات:**\n"
        "- التحميل قد يستغرق بعض الوقت.\n"
        "- الملفات الأكبر من 2GB قد تفشل في الرفع (حد تيليجرام).\n"
        "- يتم استخدام الكوكيز المرفقة لمحاولة تحميل الفيديوهات المقيدة بالعمر أو التي تتطلب تسجيل دخول.\n"
        "- يستخدم البوت `yt-dlp` و `FFmpeg` (إذا كان مثبتًا) للمعالجة.",
        disable_web_page_preview=True,
        quote=True
    )

# --- دالة لجلب معلومات الفيديو والصيغ المتاحة ---
# Now uses asyncio.to_thread for non-blocking execution
async def get_video_info_and_formats_async(url):
    """Fetches video info dictionary using yt-dlp in a separate thread."""
    ydl_opts = {
        'quiet': True,
        'verbose': False, # Less verbose normally
        'skip_download': True,
        'nocheckcertificate': True,
        'retries': 5, # Retries for info fetch
        'extract_flat': 'discard_in_playlist', # Faster info for playlists
        'dump_single_json': True, # Get info as a single JSON object
        'http_headers': { # Use same headers as download
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8'
        }
    }
    cookie_jar = load_cookies()
    if cookie_jar:
        ydl_opts['cookiejar'] = cookie_jar

    print(f"DEBUG: Fetching info for URL: {url} using asyncio.to_thread")

    def sync_get_info():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                print(f"DEBUG: Info fetched successfully for {url}")
                return info_dict
        except yt_dlp.utils.DownloadError as e:
            print(f"ERROR: yt-dlp failed to extract info: {e}")
            # Return a dictionary with the error string for handling
            return {"error": str(e)}
        except Exception as e:
            print(f"ERROR: General exception in sync_get_info: {type(e).__name__}: {e}")
            return {"error": f"خطأ غير متوقع في جلب المعلومات: {e}"}

    # Run the synchronous yt-dlp call in a separate thread
    return await asyncio.to_thread(sync_get_info)


# --- دالة لتصنيف وعرض الصيغ (مع تقسيم جودة الفيديو) ---
def categorize_and_prepare_formats(info_dict, media_type):
    """Prepares InlineKeyboardButtons for format selection with video quality tiers."""
    formats = info_dict.get('formats', [])
    if not formats:
        return None, "لم يتم العثور على صيغ متاحة في معلومات الفيديو."

    buttons = []
    initial_text = ""

    if media_type == 'video':
        initial_text = "🎬 اختر جودة الفيديو المطلوبة:"
        # Define quality tiers {tier_name: {label: '', selector: '', best_format: None}}
        quality_tiers = {
            "low": {"label": "ضعيفة (<= 480p)", "selector": "format_video_low", "best_format": None, "max_h": 480},
            "medium": {"label": "متوسطة (720p)", "selector": "format_video_medium", "best_format": None, "max_h": 720},
            "high": {"label": "عالية (>= 1080p)", "selector": "format_video_high", "best_format": None, "min_h": 1080},
        }
        # Dictionary to store the best format found for each available height {height: format_dict}
        available_formats_by_height = {}

        # --- Find the best format for each available height ---
        for f in formats:
            # Basic checks: needs video codec, height, and ideally extension
            height = f.get('height')
            vcodec = f.get('vcodec', 'none')
            if not height or vcodec == 'none' or vcodec == 'unknown':
                continue

            # Determine if the current format `f` is better than the existing one for this height
            is_better = False
            current_best = available_formats_by_height.get(height)
            has_audio = f.get('acodec', 'none') != 'none'
            ext = f.get('ext')
            tbr = f.get('tbr') # Total bitrate as a fallback quality measure

            if not current_best:
                is_better = True
            else:
                current_has_audio = current_best.get('acodec', 'none') != 'none'
                current_ext = current_best.get('ext')
                current_tbr = current_best.get('tbr')

                # Prioritization logic:
                # 1. Prefer combined streams (video+audio) over video-only
                if has_audio and not current_has_audio: is_better = True
                elif has_audio == current_has_audio:
                    # 2. If audio status is same, prefer mp4 extension
                    if ext == 'mp4' and current_ext != 'mp4': is_better = True
                    # 3. If extension is also same, prefer higher total bitrate (if available)
                    elif ext == current_ext and tbr and current_tbr and tbr > current_tbr: is_better = True
                    # 4. Don't replace an mp4 with another format unless the new one adds audio
                    elif current_ext == 'mp4' and ext != 'mp4' and not (has_audio and not current_has_audio):
                        is_better = False # Keep the existing mp4

            if is_better:
                available_formats_by_height[height] = f

        # --- Assign best format to each quality tier ---
        sorted_heights = sorted(available_formats_by_height.keys(), reverse=True) # Process highest first

        assigned_formats = set() # Keep track of formats assigned to prevent duplicates in different tiers

        # Assign High Tier (>= 1080p)
        for h in sorted_heights:
            if h >= quality_tiers["high"]["min_h"]:
                 fmt = available_formats_by_height[h]
                 if fmt['format_id'] not in assigned_formats:
                     quality_tiers["high"]["best_format"] = fmt
                     assigned_formats.add(fmt['format_id'])
                     break # Found the best for high tier

        # Assign Medium Tier (~720p) - find best <= 720p not already assigned to high
        for h in sorted_heights:
             if h <= quality_tiers["medium"]["max_h"]:
                  fmt = available_formats_by_height[h]
                  if fmt['format_id'] not in assigned_formats:
                      quality_tiers["medium"]["best_format"] = fmt
                      assigned_formats.add(fmt['format_id'])
                      break # Found the best for medium tier

        # Assign Low Tier (<= 480p) - find best <= 480p not already assigned
        for h in sorted_heights:
            if h <= quality_tiers["low"]["max_h"]:
                 fmt = available_formats_by_height[h]
                 if fmt['format_id'] not in assigned_formats:
                     quality_tiers["low"]["best_format"] = fmt
                     assigned_formats.add(fmt['format_id'])
                     break # Found the best for low tier

        # --- Create buttons for available tiers ---
        for tier_data in quality_tiers.values():
            fmt = tier_data.get("best_format")
            if fmt:
                height = fmt.get('height')
                ext = fmt.get('ext')
                # Use filesize_approx if filesize is missing, otherwise None
                filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                size_str = f" ({format_bytes(filesize)})" if filesize else ""
                has_audio_str = "🔊" if fmt.get('acodec', 'none') != 'none' else ""
                # Label: Tier Name - Resolution (Extension) [Size] AudioIndicator
                label = f"{tier_data['label']} - {height}p ({ext}){size_str} {has_audio_str}".strip()
                buttons.append([InlineKeyboardButton(label, callback_data=tier_data['selector'])])

        if not buttons: # Fallback if categorization failed but formats exist
            print("WARN: Video tier categorization failed, trying generic best.")
            # Offer a generic 'best' option as a last resort if tiers failed
            buttons.append([InlineKeyboardButton("أفضل جودة متاحة 🎬", callback_data="format_video_best")])
            # return None, "لم يتم العثور على صيغ فيديو مناسبة للعرض بعد التصنيف."


    elif media_type == 'audio':
        initial_text = "🔉 اختر جودة الصوت المطلوبة:"
        audio_formats = []
        # Prioritize audio-only formats first
        for f in formats:
            acodec = f.get('acodec', 'none')
            vcodec = f.get('vcodec', 'none')
            # Check for valid audio codec and no video codec
            if acodec not in ['none', None] and vcodec in ['none', None]:
                 # Optional: Check for reasonable extensions
                 if f.get('ext') in ['m4a', 'mp3', 'opus', 'ogg', 'aac', 'flac', 'wav']:
                     audio_formats.append(f)

        # If no audio-only found, consider combined formats with audio as fallback
        if not audio_formats:
            print("WARN: No audio-only formats found, considering combined formats (mp4/webm) with audio.")
            for f in formats:
                acodec = f.get('acodec', 'none')
                if acodec not in ['none', None]:
                     # Allow common video containers if they have audio
                     if f.get('ext') in ['mp4', 'm4a', 'webm']:
                         audio_formats.append(f)

        if not audio_formats:
            return None, "لم يتم العثور على أي صيغ صوتية متاحة (حتى ضمن ملفات الفيديو)."

        # Sort by audio bitrate (abr), descending. Use 0 if abr is missing.
        audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)

        # Add a "Best Quality" option first
        buttons.append([InlineKeyboardButton("أفضل جودة صوت 🏆", callback_data="format_audio_best")])

        limit = 6 # Limit the number of specific options shown
        count = 0
        added_labels = set() # To avoid showing duplicate labels (e.g., multiple ~128kbps Opus)

        for f in audio_formats:
            if count >= limit: break
            format_id = f.get('format_id')
            if not format_id: continue # Skip if format_id is missing

            ext = f.get('ext')
            abr = f.get('abr') # Audio bitrate
            acodec = f.get('acodec', 'N/A').replace('mp4a.40.2', 'aac') # Clean codec name

            # Approximate size if available
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_str = f" ({format_bytes(filesize)})" if filesize else ""

            # Create a descriptive label
            label_parts = []
            if abr: label_parts.append(f"~{abr:.0f}kbps")
            label_parts.append(acodec)
            if ext: label_parts.append(f"({ext})")
            label = " ".join(label_parts).strip() + size_str

            # Skip if label is empty or already added
            if not label or label in added_labels: continue

            buttons.append([InlineKeyboardButton(label, callback_data=f"format_audio_{format_id}")])
            added_labels.add(label)
            count += 1

    # Add Cancel button to all format selections
    if buttons: # Only add cancel if there are other options
        buttons.append([InlineKeyboardButton("➡️ العودة", callback_data="format_back_to_type")])
        buttons.append([InlineKeyboardButton("إلغاء ❌", callback_data="format_cancel")])
    else:
         # If no buttons were generated at all
         return None, f"لم يتم العثور على صيغ متاحة قابلة للعرض لـ **{media_type}**."

    reply_markup = InlineKeyboardMarkup(buttons)
    return reply_markup, initial_text

# --- معالج الرسائل النصية (روابط يوتيوب) ---
@bot.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_youtube_url(client: Client, message: filters.Message):
    """Handles incoming text messages containing YouTube URLs."""
    url = message.text.strip()
    # Slightly improved regex to better handle various URL formats including shorts, live, playlists
    youtube_regex = re.compile(
        r'(?:https?://)?'                          # Optional http(s)://
        r'(?:www\.|m\.)?'                           # Optional www. or m.
        r'(?:youtube(?:-nocookie)?\.com|youtu\.be)' # Domain variations
        r'/'                                       # Slash separator
        r'(?:watch\?v=|embed/|v/|live/|shorts/|playlist\?list=|attribution_link\?.*v%3D)?' # Path variations
        r'([a-zA-Z0-9_-]{11,})'                    # Video or Playlist ID (11+ chars)
        r'(?:[&\?].*)?'                            # Optional remaining query params
    )
    match = youtube_regex.match(url)

    if not match:
        await message.reply_text("الرابط الذي أرسلته لا يبدو كرابط يوتيوب صالح. يرجى المحاولة مرة أخرى.", quote=True)
        return

    # Use the matched ID or list parameter for cleaner URL processing if needed
    matched_id = match.group(1)
    # Reconstruct a cleaner URL (optional, but can help yt-dlp sometimes)
    if "playlist?list=" in url:
        clean_url = f"https://www.youtube.com/playlist?list={matched_id}"
    elif "/shorts/" in url or "/live/" in url:
         clean_url = f"https://www.youtube.com/watch?v={matched_id}" # Treat shorts/live like videos
    else:
        clean_url = f"https://www.youtube.com/watch?v={matched_id}"
    print(f"DEBUG: Processing URL: {url} (Cleaned: {clean_url})")


    user_id = message.from_user.id
    # --- Clear Previous Session ---
    if user_id in download_sessions:
        print(f"DEBUG: Clearing previous session for user {user_id}")
        old_session = download_sessions.pop(user_id, None)
        if old_session and old_session.get('status_message_id'):
            try:
                # Attempt to edit the old message to indicate cancellation
                await client.edit_message_text(message.chat.id, old_session['status_message_id'], "تم بدء عملية جديدة.")
                await asyncio.sleep(2) # Give user time to see
                await client.delete_messages(message.chat.id, old_session['status_message_id'])
            except (MessageIdInvalid, MessageNotModified):
                 print(f"WARN: Could not edit/delete previous status message {old_session['status_message_id']} for user {user_id}.")
            except Exception as e:
                print(f"WARN: Error deleting previous status message {old_session.get('status_message_id')}: {e}")


    status_message = await message.reply_text("🔍 جاري جلب معلومات الرابط...", quote=True)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # --- Fetch Video Info Asynchronously ---
    info_dict = await get_video_info_and_formats_async(clean_url) # Use cleaned URL

    # --- Error Handling for Info Fetch ---
    if not info_dict or isinstance(info_dict.get("error"), str):
        error_msg = info_dict.get("error", "فشل جلب معلومات الفيديو لسبب غير معروف.") if isinstance(info_dict, dict) else "فشل جلب معلومات الفيديو."
        print(f"ERROR: Info fetch failed for {url}. Raw error: {error_msg}")
        # Map common technical errors to user-friendly messages
        error_map = {
            "video unavailable": "❌ الفيديو غير متاح.",
            "private video": "❌ هذا الفيديو خاص ولا يمكن الوصول إليه.",
            "login required": "🔒 هذا المحتوى يتطلب تسجيل الدخول (قد تحتاج لتحديث الكوكيز).",
            "confirm your age": "🔞 هذا المحتوى يتطلب تأكيد العمر (قد تحتاج لتحديث الكوكيز).",
            "premiere": "⏳ الفيديو عرض أول ولم يبدأ بعد.",
            "is live": "🔴 البث المباشر غير مدعوم حاليًا للتحميل المباشر.",
            "http error 403": "🚫 خطأ 403: الوصول مرفوض (قد يكون المحتوى مقيدًا جغرافيًا أو يتطلب كوكيز).",
            "http error 404": "❓ خطأ 404: الفيديو أو قائمة التشغيل غير موجودة.",
            "http error 429": "⏳ خطأ 429: تم حظر الطلبات مؤقتًا. يرجى المحاولة لاحقًا.",
            "unable to download webpage": "🌐 تعذر الوصول إلى صفحة الويب الخاصة بالرابط.",
            "resolve host": "🌐 خطأ في الشبكة، تعذر العثور على المضيف.",
            "unsupported url": "🔗 الرابط غير مدعوم بواسطة `yt-dlp`."
        }
        user_friendly_error = f"❌ فشل جلب المعلومات:\n`{error_msg[:300]}`" # Default with raw error
        for key, friendly_msg in error_map.items():
            if key.lower() in error_msg.lower():
                user_friendly_error = friendly_msg
                break

        await status_message.edit_text(user_friendly_error)
        await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
        # Clean up session data if created prematurely
        if user_id in download_sessions: del download_sessions[user_id]
        return

    # --- Extract Metadata ---
    # Use .get() with defaults for safety
    title = info_dict.get('title', 'غير متوفر')
    thumbnail_url = info_dict.get('thumbnail')
    view_count = info_dict.get('view_count')
    duration = info_dict.get('duration')
    duration_str = td_format(duration) if duration else "غير معروف"
    # Determine if it's a playlist ('entries' exists and is a list, could be empty)
    is_playlist = info_dict.get('_type') == 'playlist' or 'entries' in info_dict
    # Count actual entries if present, otherwise assume 1 item
    item_count = len(info_dict.get('entries') or []) if is_playlist else 1
    channel_name = info_dict.get('channel', info_dict.get('uploader', 'غير معروف')) # Fallback to uploader
    upload_date_str = info_dict.get('upload_date') # YYYYMMDD
    upload_date_formatted = None
    if upload_date_str:
        try:
            from datetime import datetime
            upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
            upload_date_formatted = upload_date.strftime('%Y-%m-%d') # Format as YYYY-MM-DD
        except (ValueError, TypeError):
            upload_date_formatted = upload_date_str # Keep original if parsing fails

    # --- Prepare Caption ---
    caption = f"**{title}**\n\n"
    if is_playlist:
        caption += f"🔢 **نوع المحتوى:** قائمة تشغيل ({item_count} مقطع)\n"
    else:
         caption += f"⏱️ **المدة:** {duration_str}\n"
    caption += f"📺 **القناة:** {channel_name}\n"

    # Add view count and upload date only if available and not a playlist summary
    if not is_playlist:
        if view_count:
            caption += f"👀 **المشاهدات:** {view_count:,}\n"
        if upload_date_formatted:
            caption += f"📅 **تاريخ الرفع:** {upload_date_formatted}\n"

    caption = caption[:800].strip() # Keep caption reasonably short and clean whitespace

    # --- Prepare Media Type Selection Buttons ---
    media_type_buttons = [
        [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
        [InlineKeyboardButton("إلغاء ❌", callback_data="type_cancel")]
    ]
    markup = InlineKeyboardMarkup(media_type_buttons)
    ask_text = f"{caption}\n\n🔧 **اختر نوع التحميل:**"

    choice_message = None # Initialize choice_message
    try:
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO) # Show activity
        if thumbnail_url:
            # Send photo with caption first
            photo_msg = await message.reply_photo(
                 photo=thumbnail_url,
                 caption=caption, # Send main caption with photo
                 quote=True
            )
            # Then send the choice text separately, replying to the photo message
            choice_message = await photo_msg.reply_text(
                 "🔧 **اختر نوع التحميل:**", # Simpler text for choice prompt
                 reply_markup=markup,
                 quote=False # Don't quote the photo message itself
            )
            # Try to delete the initial "fetching info..." message silently
            try: await status_message.delete()
            except Exception: pass # Ignore if already deleted or other issue
        else:
            # If no thumbnail, edit the original status message with the full text and buttons
            await status_message.edit_text(ask_text, reply_markup=markup, disable_web_page_preview=True)
            choice_message = status_message # The status message becomes the choice message

    except Exception as e:
        print(f"ERROR: Error sending photo/caption or editing message: {e}")
        try:
            # Fallback: Edit status message or send new if status failed/deleted
            if status_message and status_message.id: # Check if status_message exists
                 await status_message.edit_text(ask_text, reply_markup=markup, disable_web_page_preview=True)
                 choice_message = status_message
            else: # If status_message is gone, send a new message
                 choice_message = await message.reply_text(ask_text, reply_markup=markup, disable_web_page_preview=True, quote=True)
        except MessageIdInvalid:
             print("WARN: Status message became invalid during fallback.")
             # Last resort: send a new message
             choice_message = await message.reply_text(ask_text, reply_markup=markup, disable_web_page_preview=True, quote=True)
        except Exception as e2:
             print(f"ERROR: Fallback message sending/editing failed: {e2}")
             await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
             # Can't interact, clean up and return
             if user_id in download_sessions: del download_sessions[user_id]
             return # Abort if we can't interact

    # --- Save Session ---
    if choice_message: # Only save session if we successfully sent a choice message
        download_sessions[user_id] = {
            'status_message_id': choice_message.id,
            'initial_text': caption, # Store the base caption text
            'choice_text': ask_text, # Store the text shown with type buttons
            'reply_markup': markup, # Store the current markup
            'url': clean_url, # Store the cleaned URL
            'info_dict': info_dict, # Store the fetched info
            'is_playlist': is_playlist,
            'item_count': item_count,
            'media_type': None, # To be filled by callback
            'format_selector': None, # To be filled by callback
            'last_download_update_time': 0,
            'last_upload_update_time': 0,
            'final_title': title, # Store for potential use in upload caption
            'final_description': info_dict.get('description', ''), # Store description
            'original_message_id': message.id, # Store original user message ID
            'original_reply_id': message.reply_to_message_id if message.reply_to_message else message.id # ID to reply to
        }
        print(f"DEBUG: Session created for user {user_id}, message {choice_message.id}")
    else:
        print(f"ERROR: Could not establish a choice message for user {user_id}. Aborting.")
        await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
        # Clean up session data if somehow created
        if user_id in download_sessions: del download_sessions[user_id]

    await client.send_chat_action(message.chat.id, ChatAction.CANCEL) # Clear "typing..." action


# Helper to format duration in HH:MM:SS or MM:SS
def td_format(seconds):
    """Formats seconds into a human-readable HH:MM:SS or MM:SS string."""
    if seconds is None: return "N/A"
    try:
        seconds = int(float(seconds)) # Ensure it's an integer
        if seconds < 0: return "N/A"
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
         return "غير معروف"


# --- معالج استعلامات ردود الفعل ---
@bot.on_callback_query()
async def format_callback(client: Client, callback_query: CallbackQuery):
    """Handles button presses for type and format selection."""
    user_id = callback_query.from_user.id
    message = callback_query.message # The message with the buttons
    session_data = download_sessions.get(user_id)

    # --- Validation ---
    if not session_data:
        try:
            await callback_query.answer("انتهت صلاحية هذه الجلسة. يرجى إرسال الرابط مرة أخرى.", show_alert=True)
            try: await message.delete() # Clean up old buttons
            except: pass
        except Exception as e: print(f"Error answering/deleting expired callback (no session): {e}")
        return

    # Check if the callback is for the *current* active message for this user
    if message.id != session_data.get('status_message_id'):
        try:
            await callback_query.answer("تم بدء عملية أخرى. هذه الأزرار لم تعد صالحة.", show_alert=True)
            # Optionally delete the now-inactive message
            try: await message.delete()
            except: pass
        except Exception as e: print(f"Error answering/deleting expired callback (wrong message): {e}")
        return

    callback_data = callback_query.data
    info_dict = session_data.get('info_dict', {}) # Should exist if session exists
    url = session_data['url']

    # --- Cancel Button ---
    if callback_data == "type_cancel" or callback_data == "format_cancel":
        print(f"DEBUG: User {user_id} cancelled operation.")
        try:
             # Edit the message to show cancellation
             await message.edit_text("❌ تم إلغاء العملية بناءً على طلبك.")
             # Delete after a short delay
             await asyncio.sleep(5)
             await message.delete()
        except MessageIdInvalid: pass # Message already gone
        except MessageNotModified: pass # Already cancelled
        except Exception as e: print(f"Error editing/deleting cancel message: {e}")
        finally:
            # Always clean up session on cancel
            if user_id in download_sessions: del download_sessions[user_id]
            await callback_query.answer("تم الإلغاء")
        return

    # --- Back Button (from format selection to type selection) ---
    if callback_data == "format_back_to_type":
         print(f"DEBUG: User {user_id} pressed Back.")
         try:
             # Restore the media type selection prompt
             media_type_buttons = [
                 [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
                 [InlineKeyboardButton("إلغاء ❌", callback_data="type_cancel")]
             ]
             markup = InlineKeyboardMarkup(media_type_buttons)
             await message.edit_text(session_data['choice_text'], reply_markup=markup)
             session_data['reply_markup'] = markup # Update session markup
             session_data['media_type'] = None # Reset chosen media type
             session_data['format_selector'] = None # Reset format selector
             await callback_query.answer("الرجاء اختيار النوع مجددًا")
         except MessageNotModified: await callback_query.answer()
         except MessageIdInvalid:
              print("WARN: Message disappeared before Back could be processed.")
              if user_id in download_sessions: del download_sessions[user_id] # Session invalid now
         except Exception as e:
              print(f"Error handling Back button: {e}")
              await callback_query.answer("حدث خطأ أثناء العودة.", show_alert=True)
         return

    # --- Handle Media Type Selection ---
    if callback_data.startswith("type_"):
        media_type = callback_data.split("_")[1] # audio or video
        session_data['media_type'] = media_type
        print(f"DEBUG: User {user_id} selected type: {media_type}")
        await callback_query.answer(f"تم اختيار {media_type}. جاري عرض الجودات المتاحة...")

        # Generate format buttons based on the selected type
        reply_markup, format_prompt_text = categorize_and_prepare_formats(info_dict, media_type)

        if reply_markup:
            session_data['format_prompt_text'] = format_prompt_text # Store the text for format buttons
            session_data['reply_markup'] = reply_markup # Update markup in session
            try:
                 await message.edit_text(format_prompt_text, reply_markup=reply_markup)
            except MessageNotModified: await callback_query.answer() # Already showing correct formats
            except MessageIdInvalid:
                 print(f"WARN: Message {message.id} became invalid before showing formats.")
                 if user_id in download_sessions: del download_sessions[user_id] # Session invalid
            except Exception as e:
                print(f"Error editing message for format selection: {e}")
                await message.edit_text("⚠️ حدث خطأ أثناء عرض الجودات المتاحة.")
                # Clean up session on error
                if user_id in download_sessions: del download_sessions[user_id]
        else:
            # If categorize_and_prepare_formats returned None (no formats found)
            await message.edit_text(f"❌ لم يتم العثور على صيغ **{media_type}** متاحة لهذا الرابط.\nقد يكون الفيديو غير متاح بهذه الصيغة أو حدث خطأ.")
            # Clean up session
            if user_id in download_sessions: del download_sessions[user_id]
        return # End processing for type selection

    # --- Handle Format Selection ---
    if callback_data.startswith("format_"):
        format_selection = callback_data.split("_", 2)[-1] # e.g., "video_low" -> "low", "audio_best" -> "best", "audio_140" -> "140"
        media_type = session_data.get('media_type')

        # Ensure media_type was selected previously
        if not media_type:
             await callback_query.answer("⚠️ خطأ: لم يتم تحديد نوع الوسائط (فيديو/صوت) أولاً.", show_alert=True)
             # Try to reset to type selection
             try:
                 media_type_buttons = [
                     [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
                     [InlineKeyboardButton("إلغاء ❌", callback_data="type_cancel")]
                 ]
                 markup = InlineKeyboardMarkup(media_type_buttons)
                 await message.edit_text(session_data['choice_text'], reply_markup=markup)
                 session_data['reply_markup'] = markup
             except Exception: pass # Ignore if reset fails
             return

        format_selector = None
        quality_name = f"{media_type} {format_selection}" # Default name

        # Determine the yt-dlp format selector string
        if media_type == 'video':
            if format_selection == "low":
                # Prefer combined mp4 <= 480p, fallback best video+audio <= 480p, fallback best anything <= 480p
                format_selector = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]"
                quality_name = "فيديو ضعيف (<=480p)"
            elif format_selection == "medium":
                # Prefer combined mp4 = 720p, fallback best video+audio = 720p, fallback best anything <= 720p
                format_selector = "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height<=720]"
                quality_name = "فيديو متوسط (720p)"
            elif format_selection == "high":
                 # Prefer combined mp4 >= 1080p, fallback best video+audio >= 1080p, fallback best anything >= 1080p, then best overall
                format_selector = "bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=1080]+bestaudio/best[height>=1080]/best"
                quality_name = "فيديو عالي (>=1080p)"
            elif format_selection == "best": # Fallback if tier buttons failed
                 format_selector = "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv+ba/b" # Prioritize mp4 combined, then best combined, then best overall
                 quality_name = "أفضل فيديو متاح"
            else:
                await callback_query.answer("⚠️ جودة فيديو غير معروفة.", show_alert=True)
                return
            print(f"DEBUG: User {user_id} selected video format '{format_selection}'. Selector: {format_selector}")

        elif media_type == 'audio':
            if format_selection == "best":
                # Let yt-dlp choose the best audio-only stream, fallback to best audio in combined
                format_selector = "bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio/best[acodec!=none]"
                quality_name = "أفضل جودة صوت"
            else:
                # Specific audio format ID was selected (e.g., "140")
                format_selector = format_selection # Use the format ID directly
                # Try to find the label for the answer message
                found_fmt = next((f for f in info_dict.get('formats', []) if f.get('format_id') == format_selection), None)
                if found_fmt:
                     abr = found_fmt.get('abr')
                     acodec = found_fmt.get('acodec', '').replace('mp4a.40.2', 'aac')
                     ext = found_fmt.get('ext')
                     quality_name = f"{acodec} (~{abr:.0f}kbps {ext})" if abr else f"{acodec} ({ext})"
                else:
                     quality_name = f"صيغة صوت {format_selection}"
            print(f"DEBUG: User {user_id} selected audio format '{format_selection}'. Selector: {format_selector}")

        else:
            await callback_query.answer("⚠️ نوع وسائط غير صالح.", show_alert=True)
            return

        # Store the chosen selector
        session_data['format_selector'] = format_selector

        # Acknowledge selection and update message
        await callback_query.answer(f"⏳ جاري بدء تحميل {quality_name}...")
        try:
            # Edit message to show "Preparing download..." and remove buttons
            prep_text = f"{session_data['initial_text']}\n\n**⏳ جارٍ التحضير للتحميل...**\n({quality_name})"
            await message.edit_text(prep_text, reply_markup=None)
            session_data['reply_markup'] = None # Clear buttons in session
            session_data['initial_text'] = prep_text # Update base text for progress hook
        except MessageIdInvalid:
            print(f"WARN: Message {message.id} was deleted before download could start.")
            if user_id in download_sessions: del download_sessions[user_id]
            return
        except MessageNotModified: pass # Already showing preparing text
        except Exception as e:
            print(f"Error editing message before download: {e}")
            # Continue anyway, but log the error

        # --- Start Download in Thread ---
        download_task = asyncio.create_task(
            asyncio.to_thread(
                download_youtube_content,
                url, message, format_selector, user_id, media_type
            )
        )

        try:
            # Wait for the download function to complete
            video_files, error_message, final_title, final_description = await download_task

            # Update session with potentially refined title/description from download function
            session_data['final_title'] = final_title
            session_data['final_description'] = final_description

        except Exception as e:
             # This catches errors within the download_youtube_content *itself*
             # yt-dlp DownloadErrors are caught *inside* download_youtube_content
             print(f"FATAL ERROR: Exception during download thread execution: {type(e).__name__}: {e}")
             import traceback
             traceback.print_exc()
             video_files = []
             error_message = f"حدث خطأ فادح وغير متوقع أثناء عملية التحميل: {e}"

        # --- Handle Download Result ---
        if error_message:
            error_display_text = f"❌ حدث خطأ أثناء التنزيل:\n\n`{error_message}`"
            try:
                await message.edit_text(error_display_text)
                # Keep error message for a bit longer
                await asyncio.sleep(15)
                await message.delete()
            except MessageIdInvalid: pass # Message already gone
            except MessageNotModified: pass # Already showing error
            except Exception as e:
                 print(f"Error displaying/deleting download error message: {e}")
                 # Try sending as new message if edit failed
                 try: await client.send_message(message.chat.id, error_display_text, reply_to_message_id=session_data.get('original_reply_id'))
                 except Exception as e2: print(f"Failed to send error message as new: {e2}")
            finally:
                 if user_id in download_sessions: del download_sessions[user_id] # Clean up session
            return # Stop processing

        if not video_files:
             error_display_text = "❌ فشل التحميل ولم يتم العثور على أي ملفات صالحة."
             try:
                 await message.edit_text(error_display_text)
                 await asyncio.sleep(10)
                 await message.delete()
             except MessageIdInvalid: pass
             except MessageNotModified: pass
             except Exception as e:
                 print(f"Error displaying/deleting no-files error message: {e}")
                 try: await client.send_message(message.chat.id, error_display_text, reply_to_message_id=session_data.get('original_reply_id'))
                 except Exception as e2: print(f"Failed to send no-files error message as new: {e2}")
             finally:
                 if user_id in download_sessions: del download_sessions[user_id] # Clean up session
             return # Stop processing

        # --- Uploading Process ---
        session_data['video_files'] = video_files
        total_files_count = len(video_files)
        upload_errors = []
        # Update initial text for upload progress
        session_data['initial_text'] = f"✅ **{session_data.get('final_title', 'الملف')}**\n   - اكتمل التحميل، جارٍ الرفع..."

        # Reply to the original user message or its reply
        reply_to_id = session_data.get('original_reply_id')

        for i, file_path in enumerate(video_files):
            if not os.path.exists(file_path):
                print(f"ERROR: File does not exist before upload attempt: {file_path}")
                upload_errors.append(f"الملف المجدول `{os.path.basename(file_path)}` غير موجود على القرص.")
                continue

            file_size = os.path.getsize(file_path)
            file_name_display = os.path.basename(file_path)
            print(f"DEBUG: Attempting to upload file {i+1}/{total_files_count}: {file_path} (Size: {format_bytes(file_size)})")

            # --- Telegram File Size Limit Check ---
            TG_MAX_SIZE = 2 * 1024 * 1024 * 1024 # 2GB
            if file_size > TG_MAX_SIZE:
                error_txt = f"❌ حجم الملف `{file_name_display}` ({format_bytes(file_size)}) يتجاوز حد تيليجرام (2GB) ولا يمكن رفعه."
                print(f"ERROR: {error_txt}")
                try:
                    # Send error message about size limit
                    await client.send_message(message.chat.id, error_txt, reply_to_message_id=reply_to_id)
                except Exception as send_err:
                    print(f"Error sending size limit message: {send_err}")
                upload_errors.append(f"الملف `{file_name_display}` كبير جدًا (> 2GB).")
                # Clean up the oversized file
                try:
                    os.remove(file_path)
                    print(f"DEBUG: Removed oversized file: {file_path}")
                except OSError as e:
                    print(f"Error removing oversized file {file_path}: {e}")
                continue # Skip to the next file

            # --- Prepare Metadata (Duration, Dimensions, Thumbnail) ---
            thumb_path = None; duration = 0; width = 0; height = 0
            if FFMPEG_AVAILABLE: # Only attempt if ffmpeg-python is installed
                try:
                    print(f"DEBUG: Probing file for metadata using ffmpeg: {file_path}")
                    probe = ffmpeg.probe(file_path)
                    format_info = probe.get('format', {})
                    # Get duration from format first, fallback to stream
                    duration = int(float(format_info.get('duration', 0)))

                    # Find the primary video or audio stream
                    stream_info = next((s for s in probe.get('streams', []) if s.get('codec_type') == ('video' if media_type == 'video' else 'audio')), None)

                    if stream_info:
                         # Prefer stream duration if format duration is zero or missing
                         stream_duration_str = stream_info.get('duration')
                         if stream_duration_str and (duration == 0 or duration is None):
                              try: duration = int(float(stream_duration_str))
                              except (ValueError, TypeError): pass # Ignore if stream duration isn't valid

                         if media_type == 'video':
                             width = int(stream_info.get('width', 0))
                             height = int(stream_info.get('height', 0))
                             # Generate thumbnail near the start (e.g., 10% in or 1s min)
                             thumb_ss = max(1, int(duration * 0.1)) if duration > 0 else 1
                             thumb_path = f"{os.path.splitext(file_path)[0]}_thumb.jpg"
                             try:
                                 print(f"DEBUG: Generating thumbnail for {file_path} at {thumb_ss}s")
                                 (ffmpeg
                                  .input(file_path, ss=thumb_ss)
                                  .output(thumb_path, vframes=1, loglevel="error") # Quieter ffmpeg logs
                                  .overwrite_output()
                                  .run(capture_stdout=True, capture_stderr=True)) # Capture output

                                 # Check if thumbnail was actually created and has size
                                 if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                                     print(f"WARN: Thumbnail generation resulted in empty file for {file_path}.")
                                     thumb_path = None
                                 else:
                                     print(f"DEBUG: ffmpeg thumbnail generated successfully: {thumb_path}")
                             except ffmpeg.Error as ff_err:
                                 # Log stderr for debugging if thumbnail fails
                                 print(f"WARN: ffmpeg thumbnail generation failed for {file_path}: {ff_err.stderr.decode()}")
                                 thumb_path = None
                             except Exception as thumb_err:
                                 print(f"ERROR: Unexpected error during thumbnail generation: {thumb_err}")
                                 thumb_path = None
                         elif media_type == 'audio':
                              # Duration already extracted, no width/height needed
                              pass
                    else:
                         print(f"WARN: Could not find primary {media_type} stream in probe for {file_path}")

                except ffmpeg.Error as ff_err:
                    # Log probe errors
                    print(f"WARN: ffprobe error for {file_path}: {ff_err.stderr.decode()}")
                except Exception as meta_err:
                    # Catch other unexpected errors during metadata extraction
                    print(f"WARN: General metadata extraction error for {file_path}: {meta_err}")
            else: # ffmpeg-python not available
                 print("DEBUG: ffmpeg-python not available, using basic metadata from yt-dlp info.")
                 # Fallback to metadata from initial info_dict if ffmpeg failed/unavailable
                 stored_info = session_data.get('info_dict', {})
                 # Find corresponding entry if playlist
                 entry_info = stored_info
                 if session_data.get('is_playlist'):
                      # Try matching by filename (less reliable) or index if possible
                      # This part is tricky without a clear link between file and entry
                      entry_info = (stored_info.get('entries') or [])[i] if i < len(stored_info.get('entries') or []) else stored_info

                 if duration == 0: duration = int(float(entry_info.get('duration', 0)))
                 if media_type == 'video':
                     if width == 0: width = int(entry_info.get('width', 0))
                     if height == 0: height = int(entry_info.get('height', 0))

            # Basic validation for metadata
            duration = max(0, duration if duration else 0)
            width = max(0, width if width else 0)
            height = max(0, height if height else 0)

            # --- Prepare Upload Caption ---
            current_title = session_data.get('final_title', os.path.splitext(file_name_display)[0]) # Use filename base as fallback title
            # Add playlist numbering if needed
            playlist_caption_part = f" | جزء {i+1}/{total_files_count}" if total_files_count > 1 else ""
            # Construct caption - Title | Part X/Y \n\n Bot Username
            caption = f"**{current_title}{playlist_caption_part}**\n\n"
            # Add description only for single files, keep it short
            # current_description = session_data.get('final_description', '')
            # if total_files_count == 1 and current_description:
            #      caption += f"{current_description[:200]}{'...' if len(current_description) > 200 else ''}\n\n"

            caption += f"تم التحميل بواسطة @{client.me.username}"
            caption = caption[:1020] # Ensure caption fits within Telegram limits

            # --- Send File ---
            last_exception = None # To store the last exception for potential document fallback
            try:
                 # Use send_chat_action for visual feedback during upload preparation
                 await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO if media_type == 'video' else ChatAction.UPLOAD_AUDIO)

                 if media_type == 'video':
                     await client.send_video(
                         chat_id=message.chat.id,
                         video=file_path,
                         caption=caption,
                         thumb=thumb_path, # Will be None if generation failed
                         duration=duration,
                         width=width,
                         height=height,
                         supports_streaming=True, # Enable streaming if possible
                         progress=upload_progress_callback,
                         progress_args=(message, user_id, file_path, i + 1, total_files_count), # Pass necessary args
                         reply_to_message_id=reply_to_id
                     )
                 elif media_type == 'audio':
                     # Extract title/performer for audio metadata
                     # Use sanitized title as base, limit length
                     extracted_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', session_data.get('final_title', 'Audio'))[:60]
                     # Use channel/uploader name as performer
                     performer = session_data.get('info_dict', {}).get('channel', session_data.get('info_dict', {}).get('uploader', 'Unknown'))[:60]

                     await client.send_audio(
                         chat_id=message.chat.id,
                         audio=file_path,
                         caption=caption,
                         title=extracted_title,
                         performer=performer,
                         thumb=thumb_path, # Use generated thumb if available
                         duration=duration,
                         progress=upload_progress_callback,
                         progress_args=(message, user_id, file_path, i + 1, total_files_count),
                         reply_to_message_id=reply_to_id
                     )
                 print(f"DEBUG: Successfully uploaded {file_path} as {media_type}")
                 last_exception = None # Reset exception on success

            except FloodWait as fw:
                 print(f"FloodWait during upload: Waiting {fw.value}s...")
                 await client.send_chat_action(message.chat.id, ChatAction.CANCEL) # Clear action during wait
                 await asyncio.sleep(fw.value + 1)
                 # Retry logic simplified: just try again once after the wait
                 try:
                      # Resend chat action before retry
                      await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO if media_type == 'video' else ChatAction.UPLOAD_AUDIO)
                      if media_type == 'video':
                          await client.send_video(message.chat.id, video=file_path, caption=caption, thumb=thumb_path, duration=duration, width=width, height=height, supports_streaming=True, progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count), reply_to_message_id=reply_to_id)
                      else:
                          await client.send_audio(message.chat.id, audio=file_path, caption=caption, title=extracted_title, performer=performer, thumb=thumb_path, duration=duration, progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count), reply_to_message_id=reply_to_id)
                      print(f"DEBUG: Successfully uploaded {file_path} on retry.")
                      last_exception = None
                 except Exception as retry_err:
                      print(f"ERROR: Upload retry failed for {file_path}: {retry_err}")
                      upload_errors.append(f"فشل إرسال `{file_name_display}` بعد انتظار FloodWait.")
                      last_exception = retry_err # Store the retry error
            except Exception as upload_err:
                print(f"ERROR: Failed to send {file_path} as {media_type}: {upload_err}")
                upload_errors.append(f"فشل إرسال `{file_name_display}` كملف {media_type}.")
                last_exception = upload_err # Store the error

            # --- Fallback to Document ---
            # If sending as Video/Audio failed (last_exception is not None)
            # Or if metadata was missing (optional, could force document if duration/dims are zero)
            force_document = (width == 0 or height == 0) and media_type == 'video' # Example condition
            if last_exception: # or force_document:
                 print(f"WARN: Falling back to sending {file_path} as document. Reason: {last_exception or 'Forced'}")
                 try:
                     # Let user know we're trying document
                     doc_fallback_text = f"{session_data['initial_text']}\n\n⚠️ تعذر الإرسال كـ{media_type}، جارٍ المحاولة كمستند..."
                     await client.edit_message_text(message.chat.id, session_data['status_message_id'], doc_fallback_text)

                     await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
                     await client.send_document(
                         chat_id=message.chat.id,
                         document=file_path,
                         caption=caption, # Use the same caption
                         thumb=thumb_path, # Still try to use thumb
                         force_document=True, # Explicitly send as document
                         progress=upload_progress_callback,
                         progress_args=(message, user_id, file_path, i + 1, total_files_count),
                         reply_to_message_id=reply_to_id
                     )
                     print(f"DEBUG: Successfully uploaded {file_path} as document (fallback).")
                     # Remove the specific error if document fallback succeeded
                     # Find and remove the error related to this file
                     error_to_remove = f"فشل إرسال `{file_name_display}` كملف {media_type}."
                     if error_to_remove in upload_errors:
                          upload_errors.remove(error_to_remove)
                          upload_errors.append(f"تم إرسال `{file_name_display}` كمستند بدلاً من {media_type}.")


                 except FloodWait as fw_doc:
                      print(f"FloodWait during document fallback: Waiting {fw_doc.value}s...")
                      await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
                      await asyncio.sleep(fw_doc.value + 1)
                      # Simple retry for document
                      try:
                         await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
                         await client.send_document(message.chat.id, document=file_path, caption=caption, thumb=thumb_path, force_document=True, progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count), reply_to_message_id=reply_to_id)
                         print(f"DEBUG: Successfully uploaded {file_path} as document on retry.")
                         error_to_remove = f"فشل إرسال `{file_name_display}` كملف {media_type}."
                         if error_to_remove in upload_errors: upload_errors.remove(error_to_remove)
                         upload_errors.append(f"تم إرسال `{file_name_display}` كمستند بدلاً من {media_type}.")
                      except Exception as doc_retry_err:
                         print(f"ERROR: Document fallback retry failed for {file_path}: {doc_retry_err}")
                         if error_to_remove not in upload_errors: # Ensure original error is logged if fallback fails completely
                             upload_errors.append(error_to_remove)
                         upload_errors.append(f"فشل إرسال `{file_name_display}` كمستند أيضًا.")

                 except Exception as doc_err:
                     print(f"ERROR: Failed to send {file_path} as Document fallback: {doc_err}")
                     # Ensure the original error remains logged if fallback also fails
                     if error_to_remove not in upload_errors:
                         upload_errors.append(error_to_remove)
                     upload_errors.append(f"فشل إرسال `{file_name_display}` كمستند أيضًا.")

            # --- Cleanup After Each File Upload Attempt ---
            finally:
                 # Clear chat action after each attempt
                 try: await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
                 except: pass
                 # Remove the local file
                 if os.path.exists(file_path):
                     try:
                         os.remove(file_path)
                         print(f"DEBUG: Removed local file: {file_path}")
                     except OSError as e:
                         print(f"Error removing uploaded file {file_path}: {e}")
                 # Remove the local thumbnail
                 if thumb_path and os.path.exists(thumb_path):
                     try:
                         os.remove(thumb_path)
                         print(f"DEBUG: Removed local thumbnail: {thumb_path}")
                     except OSError as e:
                         print(f"Error removing thumbnail file {thumb_path}: {e}")

        # --- Final Status Update ---
        final_status_text = ""
        status_message_id = session_data.get('status_message_id')

        if upload_errors:
            final_status_text = f"⚠️ اكتملت العملية مع {len(upload_errors)} خطأ:\n\n- " + "\n- ".join(upload_errors)
            final_status_text = final_status_text[:4000] # Limit length
        else:
            final_status_text = f"✅ تم رفع جميع الملفات ({total_files_count}) بنجاح!"

        print(f"DEBUG: Final status for user {user_id}: {final_status_text}")

        if status_message_id: # If status message still exists
            try:
                # Try to edit the status message with the final result
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message_id,
                    text=final_status_text
                )
                # Optionally delete the status message after a delay
                await asyncio.sleep(15 if upload_errors else 10) # Keep errors longer
                await client.delete_messages(message.chat.id, status_message_id)
                session_data['status_message_id'] = None # Mark as deleted
            except (MessageIdInvalid, MessageNotModified): # Message might be gone or unchanged
                print("WARN: Final status message was gone or unchanged before final edit/delete.")
                # Send as new message if editing failed
                try:
                     await client.send_message(message.chat.id, final_status_text, reply_to_message_id=reply_to_id)
                except Exception as final_send_err:
                     print(f"Error sending final status as new message: {final_send_err}")
            except Exception as e:
                print(f"Error editing/deleting final status message: {e}")
                # Send as new message if editing failed
                try:
                    await client.send_message(message.chat.id, final_status_text, reply_to_message_id=reply_to_id)
                except Exception as final_send_err:
                    print(f"Error sending final status as new message after edit error: {final_send_err}")
        else: # If status message was already gone
             print("DEBUG: Status message ID was None, sending final status as new message.")
             try:
                 await client.send_message(message.chat.id, final_status_text, reply_to_message_id=reply_to_id)
             except Exception as final_send_err:
                 print(f"Error sending final status as new message (ID was None): {final_send_err}")


        # Clean up session data for the user
        if user_id in download_sessions:
            del download_sessions[user_id]
            print(f"DEBUG: Session closed for user {user_id}.")

    # --- Fallback Acknowledge ---
    # Acknowledge other button presses silently if not handled above
    # (Shouldn't happen with current logic, but good practice)
    else:
         try: await callback_query.answer()
         except Exception: pass


# --- دالة عرض تقدم الرفع ---
async def upload_progress_callback(current, total, message, user_id, file_path, file_index, total_files):
    """Updates the status message with upload progress."""
    session_data = download_sessions.get(user_id)
    status_message_id = session_data.get('status_message_id') if session_data else None

    # Exit if session is gone or message ID is unknown
    if not session_data or not status_message_id:
        # print(f"DEBUG: Upload progress skipped for user {user_id} - no session or message ID.")
        return

    now = time.time()
    last_update = session_data.get('last_upload_update_time', 0)
    # Throttle updates to avoid FloodWait
    if now - last_update < 1.5: # 1.5 second throttle
        return
    session_data['last_upload_update_time'] = now

    try:
        percentage = current / total if total > 0 else 0
        progress_bar_str = progress_bar_generator(percentage)
        file_name_display = os.path.basename(file_path)
        current_size_str = format_bytes(current)
        total_size_str = format_bytes(total)
        playlist_info = f" (ملف {file_index}/{total_files})" if total_files > 1 else ""

        # Use the initial text stored in the session which should indicate download complete
        base_text = session_data.get('initial_text', '✅ اكتمل التحميل.')

        progress_text = (
            f"{base_text}\n\n"
            f"**⬆️ جاري الرفع{playlist_info}:**\n"
            # Limit filename display length in progress
            f"`{file_name_display[:45]}{'...' if len(file_name_display)>45 else ''}`\n"
            f" {progress_bar_str} ({percentage*100:.1f}%)\n"
            f" {current_size_str} / {total_size_str}"
        )

        # Edit the status message
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message_id,
            text=progress_text
        )
    except MessageNotModified:
        # print("DEBUG: Message not modified (upload progress)")
        pass
    except FloodWait as fw:
        print(f"FloodWait in upload_progress: Waiting {fw.value}s...")
        await asyncio.sleep(fw.value + 1) # Wait and potentially retry implicitly on next callback
    except MessageIdInvalid:
        print(f"WARN: Upload progress - Status message ID {status_message_id} invalid. Clearing from session.")
        if user_id in download_sessions:
            download_sessions[user_id]['status_message_id'] = None # Stop trying to edit
    except Exception as e:
        print(f"ERROR in upload_progress_callback: {type(e).__name__}: {e}")
        if user_id in download_sessions:
            download_sessions[user_id]['status_message_id'] = None # Stop trying to edit


# --- تشغيل البوت ---
if __name__ == "__main__":
    print("INFO: Initializing bot...")
    # Test loading cookies on startup
    print("INFO: Testing cookie loading...")
    initial_cookies = load_cookies()
    if initial_cookies:
        print(f"INFO: Cookies loaded successfully on startup. Found {len(initial_cookies)} cookies.")
    else:
        print("WARN: Could not load cookies on startup or cookie variable is empty.")

    # Test for FFmpeg
    if FFMPEG_AVAILABLE:
        print("INFO: ffmpeg-python library is available.")
    else:
        print("WARN: ffmpeg-python library not found. Install it (`pip install ffmpeg-python`) for better metadata and thumbnails.")

    print("INFO: Starting bot polling...")
    try:
        # bot.run() uses asyncio.run() internally
        bot.run()
    except ValueError as ve:
         # Catch the specific error for missing env vars
         print(f"FATAL ERROR: {ve}")
    except Exception as e:
        print(f"FATAL ERROR: Bot crashed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("INFO: Bot stopped.")
