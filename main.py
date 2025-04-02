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
import glob # Import glob for file finding fallback
import time # Import time for throttling
import ffmpeg # Import ffmpeg for metadata (optional but recommended)

# --- بيانات البوت ---
API_ID = os.environ.get("API_ID", )
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

bot = Client(
    "URL UPLOADER BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- مجلد التحميل ---
DOWNLOAD_FOLDER = "./downloads/"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"DEBUG: Created download folder: {DOWNLOAD_FOLDER}")

# --- قاموس لتخزين بيانات التنزيل المؤقتة ---
download_sessions = {}

# --- ملف الكوكيز ---
YTUB_COOKIES_CONTENT = os.environ.get("YTUB_COOKIES", """
Netscape HTTP Cookie File
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	TRUE	1758115994	VISITOR_INFO1_LIVE	MHCsPCRDwfQ
# ... (rest of your cookies) ...
.youtube.com	TRUE	/	TRUE	0	YSC	FdDjnHg1lag
"""
)

# --- دالة مساعد لتحميل الكوكيز ---
def load_cookies():
    cookie_jar = http.cookiejar.MozillaCookieJar()
    if YTUB_COOKIES_CONTENT and YTUB_COOKIES_CONTENT.strip():
        try:
            cookie_jar.load(StringIO(YTUB_COOKIES_CONTENT), ignore_discard=True, ignore_expires=True)
            print("DEBUG: Cookies loaded successfully from variable.")
            return cookie_jar
        except Exception as e:
            print(f"DEBUG: Error loading cookies from variable: {e}. Proceeding without cookies.")
            return None
    else:
        print("DEBUG: YTUB_COOKIES variable is empty. Proceeding without cookies.")
        return None

# --- دالة تنسيق حجم الملف ---
def format_bytes(size):
    if size is None or size == 0:
       return "0 B"
    try:
        size = float(size)
        if size == 0: return "0 B" # Handle zero after conversion
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        # Ensure index is within bounds
        i = max(0, min(len(size_name) - 1, i))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return f"{s} {size_name[i]}"
    except (ValueError, TypeError, OverflowError):
        return "N/A"


# --- دالة تنزيل الفيديو/قائمة التشغيل ---
def download_youtube_content(url, message, format_selector, user_id, media_type):
    print(f"DEBUG: Starting download for URL: {url}, format_selector: {format_selector}, type: {media_type}")
    # --- Sanitize Title ---
    try:
        pre_ydl_opts = {'quiet': True, 'skip_download': True, 'nocheckcertificate': True}
        cookie_jar_pre = load_cookies()
        if cookie_jar_pre: pre_ydl_opts['cookiejar'] = cookie_jar_pre
        with yt_dlp.YoutubeDL(pre_ydl_opts) as ydl_pre:
            info_pre = ydl_pre.extract_info(url, download=False)
            base_title = info_pre.get('title', 'youtube_download')
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "", base_title)[:100]
            original_ext = info_pre.get('ext')
            final_title = info_pre.get('title', 'محتوى يوتيوب')
            final_description = info_pre.get('description', 'لا يوجد وصف')
    except Exception as e:
        print(f"DEBUG: Error fetching initial info for sanitization: {e}. Using default title.")
        sanitized_title = f"youtube_download_{user_id}_{int(time.time())}"
        original_ext = 'mp4'
        final_title = 'محتوى يوتيوب'
        final_description = 'لا يوجد وصف'

    # --- Prepare yt-dlp Options ---
    cookie_jar = load_cookies()
    output_template_base = os.path.join(DOWNLOAD_FOLDER, sanitized_title)
    final_expected_ext = 'mp4' # Default for video

    ydl_opts = {
        'progress_hooks': [lambda d: asyncio.run(progress_hook(d, message, user_id))], # Ensure hook is run in event loop
        'format': format_selector,
        'verbose': True,
        'retries': 10,
        'fragment_retries': 10,
        'http_chunk_size': 10 * 1024 * 1024,
        'nocheckcertificate': True,
        'prefer_ffmpeg': True,
        'postprocessors': [],
        'outtmpl': f'{output_template_base}.%(ext)s',
        'keepvideo': False,
        'concurrent_fragment_downloads': 5,
        # Merge into mp4 if separate streams are downloaded
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    }
    if cookie_jar: ydl_opts['cookiejar'] = cookie_jar

    if media_type == 'audio':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
        ydl_opts['outtmpl'] = f'{output_template_base}.mp3'
        final_expected_ext = 'mp3'
    else: # Video
         # Ensure yt-dlp tries merging into mp4 when downloading separate video/audio streams
         ydl_opts['outtmpl'] = f'{output_template_base}.%(ext)s' # Let ext be determined first
         final_expected_ext = 'mp4' # Because we set merge_output_format

    # --- Execute Download ---
    downloaded_files = []
    error_message = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"DEBUG: Running yt-dlp with options: {ydl_opts}")
            info_dict = ydl.extract_info(url, download=True)
            print(f"DEBUG: yt-dlp finished execution.")

            # --- Locate Downloaded File(s) ---
            # Update title/description from the *final* info_dict after potential playlist processing
            final_title = info_dict.get('title', final_title)
            final_description = info_dict.get('description', final_description)
            is_playlist = 'entries' in info_dict

            if is_playlist:
                print(f"DEBUG: Processing playlist results ({len(info_dict['entries'])} entries)...")
                for entry in info_dict.get('entries', []):
                    if not entry: continue # Skip None entries if any
                    # Use 'filepath' if available (after processing)
                    filepath = entry.get('filepath')
                    entry_title_raw = entry.get('title', f'playlist_entry_{entry.get("id", "unknown")}')
                    entry_sanitized = re.sub(r'[\\/*?:"<>|]', "", entry_title_raw)[:100]
                    entry_base = os.path.join(DOWNLOAD_FOLDER, entry_sanitized)
                    entry_expected_ext = final_expected_ext if media_type == 'audio' else entry.get('ext', final_expected_ext)
                    expected_path = f"{entry_base}.{entry_expected_ext}"

                    found_path = None
                    if filepath and os.path.exists(filepath):
                         found_path = filepath
                         print(f"DEBUG: Found playlist file via 'filepath': {found_path}")
                    elif os.path.exists(expected_path):
                         found_path = expected_path
                         print(f"DEBUG: Found playlist file via constructed path: {found_path}")
                    else: # Fallback check common extensions for video
                         if media_type == 'video':
                              for ext_guess in ['mp4', 'mkv', 'webm']:
                                   fallback_path = f"{entry_base}.{ext_guess}"
                                   if os.path.exists(fallback_path):
                                        found_path = fallback_path
                                        print(f"DEBUG: Found playlist video file via fallback '{ext_guess}': {found_path}")
                                        break
                    if found_path:
                         downloaded_files.append(found_path)
                    else:
                         print(f"WARN: Cannot find downloaded file for playlist entry: '{entry_title_raw}'")

            else: # Single video
                print("DEBUG: Processing single video result...")
                filepath = info_dict.get('filepath') # Final path after processing
                expected_path = f"{output_template_base}.{final_expected_ext}"

                found_path = None
                if filepath and os.path.exists(filepath):
                    found_path = filepath
                    print(f"DEBUG: Found single file via 'filepath': {found_path}")
                elif os.path.exists(expected_path):
                    found_path = expected_path
                    print(f"DEBUG: Found single file via constructed path: {found_path}")
                else: # Fallback check common extensions
                     extensions_to_check = ['mp4', 'mkv', 'webm'] if media_type == 'video' else ['mp3']
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
                    print(f"ERROR: Could not find final file for '{final_title}' at '{expected_path}' or common fallbacks.")

    # ... (rest of error handling as before) ...
    except yt_dlp.utils.DownloadError as e:
        print(f"ERROR: yt-dlp download failed: {e}")
        error_str = str(e).lower() # Lowercase for easier checking
        if "unsupported url" in error_str: error_message = "الرابط غير مدعوم."
        elif "video unavailable" in error_str: error_message = "الفيديو غير متاح."
        elif "private video" in error_str: error_message = "هذا الفيديو خاص."
        elif "login required" in error_str or "confirm your age" in error_str: error_message = "هذا الفيديو يتطلب تسجيل الدخول أو تأكيد العمر (قد تحتاج لكوكيز صالحة)."
        elif "premiere" in error_str: error_message = "الفيديو عرض أول ولم يبدأ بعد."
        elif "is live" in error_str: error_message = "البث المباشر غير مدعوم حاليًا للتحميل."
        elif "http error 403" in error_str or "forbidden" in error_str: error_message = "خطأ 403: الوصول مرفوض (قد يكون مقيدًا أو يتطلب كوكيز أحدث)."
        elif "http error 404" in error_str: error_message = "خطأ 404: الملف أو الفيديو غير موجود."
        elif "ffmpeg" in error_str and "not found" in error_str: error_message = "خطأ في المعالجة: لم يتم العثور على FFmpeg."
        elif "unable to download webpage" in error_str or "network error" in error_str: error_message = "خطأ في الشبكة أو تعذر الوصول للرابط."
        else:
            match = re.search(r'ERROR: (.*?)(?:;|$)', str(e), re.IGNORECASE)
            error_message = f"فشل التحميل: {match.group(1).strip()}" if match else f"فشل التحميل: {e}"
    except Exception as e:
        print(f"ERROR: General download exception: {e}")
        error_message = f"حدث خطأ غير متوقع: {e}"

    # Final check
    if not downloaded_files and not error_message:
        error_message = "فشل التحميل لسبب غير معروف ولم يتم العثور على ملفات."
        print("ERROR: Download finished but no files were found and no specific error recorded.")

    final_files = [f for f in downloaded_files if os.path.exists(f)]
    if len(final_files) != len(downloaded_files):
        print(f"WARN: Some initially reported files do not exist. Final list: {final_files}")

    print(f"DEBUG: Returning files: {final_files}, error: {error_message}, title: {final_title}")
    return final_files, error_message, final_title, final_description


# --- دالة عرض التقدم (Download Only) ---
async def progress_hook(d, message, user_id):
    """Updates the message with download progress."""
    session_data = download_sessions.get(user_id)
    if not session_data or session_data.get('status_message_id') != message.id: return

    now = time.time()
    last_update = session_data.get('last_download_update_time', 0)
    # Allow 'finished' and 'error' states to bypass throttling
    if d['status'] not in ['finished', 'error'] and (now - last_update < 1.5) :
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
                speed = d.get('_speed_str', "N/A")
                eta = d.get('_eta_str', "N/A")
                total_size_str = format_bytes(total_bytes)
                downloaded_size_str = format_bytes(downloaded_bytes)
                progress_bar_str = progress_bar_generator(percentage)

                filename_info = d.get('info_dict', {}).get('title', os.path.basename(d.get('filename', '')))[:50]
                playlist_index = d.get('playlist_index')
                playlist_count = d.get('playlist_count')
                playlist_info = f" (مقطع {playlist_index}/{playlist_count})" if playlist_index and playlist_count else ""

                current_text = (
                    f"**⏳ جاري التحميل{playlist_info}:**\n"
                    f"`{filename_info}...`\n"
                    f"📦 {progress_bar_str} ({percentage*100:.1f}%)\n"
                    f"💾 {downloaded_size_str} / {total_size_str}\n"
                    f"🚀 السرعة: {speed} | ⏳ المتبقي: {eta}"
                )

        elif d['status'] == 'finished':
             # Check if it's the last item in a playlist or a single video
            is_last_or_single = False
            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            if not playlist_index or playlist_index == playlist_count:
                 is_last_or_single = True

            if is_last_or_single:
                 current_text = "✅ اكتمل التحميل. جاري المعالجة والرفع..."
                 session_data['initial_text'] = "✅ اكتمل التحميل." # Update base text for upload stage
                 markup = None # Remove buttons now
            else:
                 # For intermediate playlist items, just show completion briefly in progress hook itself
                 # No need to edit the main message repeatedly for each item finish
                 filename_info = d.get('info_dict', {}).get('title', os.path.basename(d.get('filename', '')))[:50]
                 print(f"DEBUG: Playlist item {playlist_index}/{playlist_count} finished: {filename_info}")
                 return # Don't edit the main message yet

        elif d['status'] == 'error':
            print(f"ERROR: yt-dlp hook reported an error: {d}")
            error_cause = d.get('_error_cause', 'سبب غير معروف')
            current_text = f"❌ حدث خطأ أثناء التحميل: `{error_cause}`"
            markup = None
            if user_id in download_sessions: del download_sessions[user_id] # Clean up

        # Edit the message if text is generated
        if current_text:
             await message.edit_text(
                  f"{session_data.get('initial_text', '')}\n\n{current_text}" if d['status'] == 'downloading' else current_text,
                  reply_markup=markup
             )

    except MessageNotModified: pass
    except FloodWait as fw:
        print(f"FloodWait in progress_hook: Waiting {fw.value} seconds...")
        await asyncio.sleep(fw.value + 1)
    except MessageIdInvalid:
        print(f"WARN: Message ID {message.id} invalid in progress_hook.")
        if user_id in download_sessions: download_sessions[user_id]['status_message_id'] = None
    except Exception as e:
        print(f"ERROR in progress_hook: {type(e).__name__}: {e}")
        if user_id in download_sessions: download_sessions[user_id]['status_message_id'] = None


# --- دالة إنشاء شريط التقدم المرئي ---
def progress_bar_generator(percentage, bar_length=15): # Shorter bar
    percentage = max(0.0, min(1.0, float(percentage)))
    completed_blocks = int(round(bar_length * percentage))
    remaining_blocks = bar_length - completed_blocks
    return '█' * completed_blocks + '░' * remaining_blocks

# --- معالج أوامر البدء ---
@bot.on_message(filters.command(["start", "help"]) & filters.private)
async def start_command(client, message):
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
        "- الملفات الأكبر من 2GB قد تفشل في الرفع.\n"
        "- يتم استخدام الكوكيز المرفقة لمحاولة تحميل الفيديوهات المقيدة.\n"
        "- يستخدم البوت `yt-dlp` و `FFmpeg` للمعالجة.",
        disable_web_page_preview=True
    )

# --- دالة لجلب معلومات الفيديو والصيغ المتاحة ---
# (get_video_info_and_formats function remains the same as in the previous good version)
def get_video_info_and_formats(url):
    """Fetches video info dictionary using yt-dlp."""
    ydl_opts = {
        'quiet': True, 'verbose': True, 'skip_download': True,
        'nocheckcertificate': True, 'retries': 5,
        'extract_flat': 'discard_in_playlist', 'dump_single_json': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    }
    cookie_jar = load_cookies()
    if cookie_jar: ydl_opts['cookiejar'] = cookie_jar
    print(f"DEBUG: Fetching info for URL: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            print(f"DEBUG: Info fetched successfully for {url}")
            return info_dict
    except yt_dlp.utils.DownloadError as e:
        print(f"ERROR: yt-dlp failed to extract info: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"ERROR: General exception in get_video_info_and_formats: {e}")
        return {"error": f"خطأ غير متوقع في جلب المعلومات: {e}"}


# --- دالة لتصنيف وعرض الصيغ (مع تقسيم جودة الفيديو) ---
def categorize_and_prepare_formats(info_dict, media_type):
    """Prepares InlineKeyboardButtons for format selection with video quality tiers."""
    formats = info_dict.get('formats', [])
    if not formats:
        return None, "لم يتم العثور على صيغ."

    buttons = []
    initial_text = ""

    if media_type == 'video':
        initial_text = "🎬 اختر جودة الفيديو المطلوبة:"
        # Define quality tiers and their representative formats {tier: best_format_found}
        quality_tiers = {
            "low": None,    # <= 480p
            "medium": None, # 720p
            "high": None    # >= 1080p
        }
        available_formats_by_height = {}

        # Find the best format for each available height first
        for f in formats:
            height = f.get('height')
            if height and f.get('vcodec') != 'none': # Basic check for video stream
                # Prioritize combined streams > mp4 > webm > other > highest bitrate
                is_better = False
                current_best = available_formats_by_height.get(height)
                has_audio = f.get('acodec') != 'none'
                ext = f.get('ext')

                if not current_best:
                    is_better = True
                else:
                    current_has_audio = current_best.get('acodec') != 'none'
                    current_ext = current_best.get('ext')
                    # Prefer combined streams
                    if has_audio and not current_has_audio: is_better = True
                    # If audio status is same, prefer mp4
                    elif has_audio == current_has_audio:
                        if ext == 'mp4' and current_ext != 'mp4': is_better = True
                        # If extension is same, prefer higher bitrate
                        elif ext == current_ext and f.get('tbr', 0) > current_best.get('tbr', 0): is_better = True
                        # If mp4 exists, don't replace with webm unless new one has audio and old doesn't
                        elif current_ext == 'mp4' and ext != 'mp4' and not (has_audio and not current_has_audio):
                             is_better = False # Keep mp4

                if is_better:
                    available_formats_by_height[height] = f

        # Assign best format to each tier
        sorted_heights = sorted(available_formats_by_height.keys(), reverse=True)

        for height in sorted_heights:
            fmt = available_formats_by_height[height]
            if height >= 1080 and quality_tiers["high"] is None:
                quality_tiers["high"] = fmt
            if height >= 720 and quality_tiers["medium"] is None: # Can be 720p itself
                 # Check if it's *not* already assigned to high
                 if quality_tiers["high"] is None or quality_tiers["high"].get('height') != height:
                      quality_tiers["medium"] = fmt
            if height <= 480 and quality_tiers["low"] is None:
                 # Assign the highest resolution <= 480p to low tier
                 quality_tiers["low"] = fmt
                 # Don't break, let it find the highest possible within the low range if multiple exist (e.g. 480p over 360p)

        # Create buttons for available tiers
        tier_map = {
            "low": {"label": "ضعيفة (<= 480p)", "selector": "format_video_low"},
            "medium": {"label": "متوسطة (720p)", "selector": "format_video_medium"},
            "high": {"label": "عالية (>= 1080p)", "selector": "format_video_high"},
        }

        for tier, data in tier_map.items():
            fmt = quality_tiers.get(tier)
            if fmt:
                height = fmt.get('height')
                ext = fmt.get('ext')
                filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                size_str = f" ({format_bytes(filesize)})" if filesize else ""
                # More descriptive label
                label = f"{data['label']} - {height}p ({ext}){size_str}"
                buttons.append([InlineKeyboardButton(label, callback_data=data['selector'])])

        if not buttons: # Fallback if categorization failed but formats exist
            return None, "لم يتم العثور على صيغ فيديو مناسبة للعرض."


    elif media_type == 'audio':
        initial_text = "🔉 اختر جودة الصوت المطلوبة:"
        audio_formats = []
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('ext') in ['m4a', 'opus', 'mp3', 'ogg']:
                audio_formats.append(f)
        if not audio_formats:
            print("WARN: No audio-only formats found, adding combined mp4/m4a as fallback.")
            for f in formats:
                if f.get('acodec') != 'none' and f.get('ext') in ['mp4', 'm4a']:
                    audio_formats.append(f)
        if not audio_formats:
            return None, "لم يتم العثور على صيغ صوتية."

        audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
        buttons.append([InlineKeyboardButton("أفضل جودة صوت 🏆", callback_data="format_audio_best")])
        limit = 8
        count = 0
        added_labels = set()
        for f in audio_formats:
            if count >= limit: break
            format_id = f['format_id']
            ext = f.get('ext')
            abr = f.get('abr')
            acodec = f.get('acodec', 'N/A').replace('mp4a.40.2', 'aac').replace('opus', 'Opus')
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_str = f" ({format_bytes(filesize)})" if filesize else ""
            label_parts = [f"~{abr:.0f}kbps"] if abr else []
            label_parts.append(acodec)
            if ext: label_parts.append(f"({ext})")
            label = " ".join(label_parts) + size_str
            if not label or label in added_labels: continue

            buttons.append([InlineKeyboardButton(label, callback_data=f"format_audio_{format_id}")])
            added_labels.add(label)
            count += 1

    if not buttons:
         return None, f"لم يتم العثور على صيغ متاحة للعرض لـ **{media_type}**."

    buttons.append([InlineKeyboardButton("إلغاء ❌", callback_data="format_cancel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    return reply_markup, initial_text

# --- معالج الرسائل النصية (روابط يوتيوب) ---
# (handle_youtube_url function remains the same)
@bot.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_youtube_url(client, message):
    url = message.text.strip()
    # More robust regex
    youtube_regex = re.compile(
        r'(?:https?://)?(?:www\.)?(?:m\.)?'
        r'(?:youtube(?:-nocookie)?\.com|youtu\.be)'
        r'/(?:watch\?v=|embed/|v/|shorts/|playlist\?list=|live/|attribution_link\?a=)?'
        r'([\w-]{11,})' # ID
        r'(?:\S+)?'
    )
    match = youtube_regex.match(url)

    if not match:
        await message.reply_text("الرابط غير صالح. يرجى إرسال رابط يوتيوب صحيح.", quote=True)
        return

    user_id = message.from_user.id
    # Ensure previous session is cleared if user sends new link
    if user_id in download_sessions:
        try:
            old_msg_id = download_sessions[user_id].get('status_message_id')
            if old_msg_id:
                await client.delete_messages(message.chat.id, old_msg_id)
        except Exception as e:
            print(f"Warn: Could not delete previous status message {old_msg_id}: {e}")
        del download_sessions[user_id]

    status_message = await message.reply_text("🔍 جاري جلب معلومات الفيديو...", quote=True)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    info_dict = await asyncio.to_thread(get_video_info_and_formats, url)

    # --- Error Handling for Info Fetch ---
    if not info_dict or "error" in info_dict:
        error_msg = info_dict.get("error", "فشل جلب معلومات الفيديو.") if isinstance(info_dict, dict) else "فشل جلب معلومات الفيديو."
        error_map = {
            "Video unavailable": "❌ الفيديو غير متاح.",
            "Private video": "❌ هذا الفيديو خاص.",
            "confirm your age": "❌ هذا الفيديو يتطلب تسجيل الدخول وتأكيد العمر.",
            "Premiere": "⏳ الفيديو عرض أول ولم يبدأ بعد.",
            "is live": "🔴 البث المباشر غير مدعوم حاليًا للتحميل.",
            "HTTP Error 403": "❌ خطأ 403: الوصول مرفوض (قد يكون مقيدًا أو يتطلب كوكيز).",
            "HTTP Error 404": "❌ خطأ 404: الفيديو غير موجود."
        }
        for key, user_friendly_error in error_map.items():
            if key.lower() in error_msg.lower():
                error_msg = user_friendly_error
                break
        else: # If no specific error matched
             error_msg = f"حدث خطأ:\n`{error_msg}`"

        await status_message.edit_text(error_msg)
        await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
        return

    # --- Extract Metadata ---
    title = info_dict.get('title', 'غير متوفر')
    thumbnail_url = info_dict.get('thumbnail')
    view_count = info_dict.get('view_count')
    duration = info_dict.get('duration')
    duration_str = td_format(duration) if duration else "غير معروف"
    # Check if 'entries' exists and is a non-empty list
    is_playlist = isinstance(info_dict.get('entries'), list) and len(info_dict['entries']) > 0
    item_count = len(info_dict['entries']) if is_playlist else 1
    channel_name = info_dict.get('channel', 'غير معروف')
    upload_date_str = info_dict.get('upload_date') # YYYYMMDD
    upload_date_formatted = None
    if upload_date_str:
        try:
            from datetime import datetime
            upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
            upload_date_formatted = upload_date.strftime('%Y-%m-%d') # Format as YYYY-MM-DD
        except ValueError:
            upload_date_formatted = upload_date_str # Keep original if parsing fails

    # --- Prepare Caption ---
    caption = f"**{title}**\n\n"
    caption += f"📺 **القناة:** {channel_name}\n"
    if is_playlist:
        caption += f"🔢 **عدد المقاطع:** {item_count}\n"
    else:
         caption += f"⏱️ **المدة:** {duration_str}\n"
         if view_count:
             caption += f"👀 **المشاهدات:** {view_count:,}\n"
         if upload_date_formatted:
             caption += f"📅 **تاريخ الرفع:** {upload_date_formatted}\n"

    caption = caption[:800] # Keep caption shorter

    # --- Send Thumbnail & Ask Type ---
    media_type_buttons = [
        [InlineKeyboardButton("صوت 🔉", callback_data="type_audio"), InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
        [InlineKeyboardButton("إلغاء ❌", callback_data="type_cancel")]
    ]
    markup = InlineKeyboardMarkup(media_type_buttons)
    ask_text = f"{caption}\n\n🔧 **اختر نوع التحميل:**"

    choice_message = None # Initialize choice_message
    try:
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        if thumbnail_url:
             photo_msg = await message.reply_photo(
                 photo=thumbnail_url,
                 caption=caption,
                 quote=True
             )
             # Now send the choice text separately, replying to the photo message
             choice_message = await photo_msg.reply_text(
                 "🔧 **اختر نوع التحميل:**",
                 reply_markup=markup,
                 quote=False # Don't quote the photo message itself
             )
             # Attempt to delete the initial "fetching info" message
             try: await status_message.delete()
             except Exception: pass # Ignore if already deleted or other issue
        else:
            # If no thumbnail, edit the original status message
            await status_message.edit_text(ask_text, reply_markup=markup, disable_web_page_preview=True)
            choice_message = status_message # The status message becomes the choice message

    except Exception as e:
        print(f"DEBUG: Error sending photo/caption or editing message: {e}")
        try:
            # Fallback: Edit status message or send new if status failed
            await status_message.edit_text(ask_text, reply_markup=markup, disable_web_page_preview=True)
            choice_message = status_message
        except Exception as e2:
             print(f"DEBUG: Fallback message edit failed: {e2}")
             try:
                 # Last resort: send a new message
                 choice_message = await message.reply_text(ask_text, reply_markup=markup, disable_web_page_preview=True, quote=True)
             except Exception as e3:
                  print(f"ERROR: Failed to send any message to user {user_id}: {e3}")
                  await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
                  return # Abort if we can't interact

    # --- Save Session ---
    if choice_message: # Only save session if we successfully sent a choice message
        download_sessions[user_id] = {
            'status_message_id': choice_message.id,
            'initial_text': caption, # Store the caption text for reference
            'reply_markup': markup,
            'url': url,
            'info_dict': info_dict,
            'is_playlist': is_playlist,
            'item_count': item_count,
            'media_type': None,
            'last_download_update_time': 0,
            'last_upload_update_time': 0,
            'final_title': title,
            'final_description': info_dict.get('description', 'لا يوجد وصف'),
        }
    await client.send_chat_action(message.chat.id, ChatAction.CANCEL)


# Helper to format duration
def td_format(seconds):
    if seconds is None: return "N/A"
    try:
        seconds = int(seconds)
        if seconds < 0: return "N/A" # Handle potential negative values
        periods = [('ساعة', 3600), ('دقيقة', 60), ('ثانية', 1)]
        strings = []
        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value > 0:
                     strings.append(f"{period_value} {period_name}")
        if not strings and seconds == 0: return "0 ثانية" # Handle exactly 0 seconds
        # If only seconds remain, include them
        if seconds > 0 and 'ثانية' not in [s.split()[-1] for s in strings]:
            strings.append(f"{seconds} ثانية")
        return ", ".join(strings) if strings else "أقل من ثانية"
    except (ValueError, TypeError):
         return "غير معروف"


# --- معالج استعلامات ردود الفعل ---
@bot.on_callback_query()
async def format_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session_data = download_sessions.get(user_id)
    message = callback_query.message

    # --- Validation ---
    if not session_data or message.id != session_data.get('status_message_id'):
        try:
            await callback_query.answer("انتهت صلاحية هذه الخيارات أو تم بدء عملية أخرى.", show_alert=True)
            try: await message.delete()
            except: pass
        except Exception as e: print(f"Error answering/deleting expired callback: {e}")
        return

    callback_data = callback_query.data
    info_dict = session_data.get('info_dict', {})

    # --- Cancel ---
    if callback_data == "type_cancel" or callback_data == "format_cancel":
        try: await message.edit_text("❌ تم إلغاء العملية.")
        except MessageIdInvalid: pass
        except Exception as e: print(f"Error editing cancel message: {e}")
        if user_id in download_sessions: del download_sessions[user_id]
        await callback_query.answer("تم الإلغاء")
        return

    # --- Handle Media Type ---
    if callback_data.startswith("type_"):
        media_type = callback_data.split("_")[1]
        session_data['media_type'] = media_type
        await callback_query.answer(f"تم اختيار {media_type}. جاري عرض الجودات...")

        reply_markup, initial_text = categorize_and_prepare_formats(info_dict, media_type)

        if reply_markup:
            session_data['initial_text'] = initial_text
            session_data['reply_markup'] = reply_markup
            try: await message.edit_text(initial_text, reply_markup=reply_markup)
            except MessageNotModified: await callback_query.answer()
            except Exception as e:
                print(f"Error editing message for format selection: {e}")
                await message.edit_text("حدث خطأ أثناء عرض الجودات.")
                if user_id in download_sessions: del download_sessions[user_id]
        else:
            await message.edit_text(f"لم يتم العثور على صيغ {media_type} متاحة.")
            if user_id in download_sessions: del download_sessions[user_id]
        return

    # --- Handle Format Selection ---
    if callback_data.startswith("format_"):
        format_selection = callback_data.split("_", 1)[1] # e.g., "video_medium", "audio_best", "audio_140"
        media_type = session_data.get('media_type')
        url = session_data['url']
        format_selector = None

        if format_selection.startswith("video_"):
            quality_tier = format_selection.split("_")[1] # low, medium, high
            # Define yt-dlp format selectors based on tier (with fallbacks)
            if quality_tier == "low":
                # Prefer combined mp4 <= 480p, fallback to best combined <= 480p, fallback to best overall <= 480p
                format_selector = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best[height<=480]"
                tier_name = "ضعيفة"
            elif quality_tier == "medium":
                # Prefer combined mp4 720p, fallback best combined 720p, fallback best <= 720p
                format_selector = "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720]/bestvideo[height<=720]+bestaudio/best[height<=720]"
                tier_name = "متوسطة"
            elif quality_tier == "high":
                 # Prefer combined mp4 >=1080p, fallback best combined >= 1080p, fallback best >= 1080p, then fallback to 720p options
                format_selector = "bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=1080]+bestaudio/best[height>=1080]/bestvideo[height=720]+bestaudio/best[height=720]/best"
                tier_name = "عالية"
            else:
                await callback_query.answer("جودة فيديو غير معروفة.", show_alert=True)
                return
            print(f"DEBUG: Video format selector for tier '{quality_tier}': {format_selector}")
            await callback_query.answer(f"⏳ جاري بدء تحميل الجودة الـ{tier_name}...")

        elif format_selection.startswith("audio_"):
            audio_format_id = format_selection.split("_")[1]
            if audio_format_id == "best":
                format_selector = "bestaudio/best" # Let yt-dlp choose best audio overall
                quality_name = "أفضل جودة صوت"
            else:
                format_selector = audio_format_id # Specific audio format ID
                # Try to find the label for the answer message
                found_fmt = next((f for f in info_dict.get('formats', []) if f.get('format_id') == audio_format_id), None)
                quality_name = f"صيغة {audio_format_id}"
                if found_fmt:
                     abr = found_fmt.get('abr')
                     acodec = found_fmt.get('acodec', '').replace('mp4a.40.2', 'aac')
                     if abr: quality_name = f"~{abr:.0f}kbps {acodec}"

            print(f"DEBUG: Audio format selector: {format_selector}")
            await callback_query.answer(f"⏳ جاري بدء تحميل {quality_name}...")

        else:
            await callback_query.answer("اختيار صيغة غير صالح.", show_alert=True)
            return

        # Update message and clear buttons
        try:
            await message.edit_text(f"{session_data['initial_text']}\n\n🚀 جارٍ التحضير للتحميل...", reply_markup=None)
            session_data['reply_markup'] = None # Clear buttons in session
        except MessageIdInvalid:
            print("WARN: Message was deleted before download could start.")
            if user_id in download_sessions: del download_sessions[user_id]
            return
        except Exception as e:
            print(f"Error editing message before download: {e}")
            # Continue anyway, but log the error

        # --- Start Download ---
        try:
            video_files, error_message, final_title, final_description = await asyncio.to_thread(
                download_youtube_content, url, message, format_selector, user_id, media_type
            )
            session_data['final_title'] = final_title
            session_data['final_description'] = final_description
        except Exception as e:
             print(f"ERROR: Exception during download thread execution: {e}")
             video_files = None
             error_message = f"حدث خطأ غير متوقع أثناء عملية التحميل: {e}"

        # --- Handle Download Result ---
        if error_message:
            try: await message.edit_text(f"❌ حدث خطأ أثناء التنزيل:\n`{error_message}`")
            except MessageIdInvalid: pass
            if user_id in download_sessions: del download_sessions[user_id]
            return
        if not video_files:
             try: await message.edit_text("❌ فشل التحميل ولم يتم العثور على ملفات.")
             except MessageIdInvalid: pass
             if user_id in download_sessions: del download_sessions[user_id]
             return

        # --- Uploading Process ---
        session_data['video_files'] = video_files
        total_files_count = len(video_files)
        upload_errors = []
        session_data['initial_text'] = f"✅ {session_data['final_title']}\n   - اكتمل التحميل بنجاح."

        for i, file_path in enumerate(video_files):
            if not os.path.exists(file_path):
                print(f"ERROR: File does not exist before upload: {file_path}")
                upload_errors.append(f"الملف `{os.path.basename(file_path)}` غير موجود.")
                continue

            file_size = os.path.getsize(file_path)
            file_name_display = os.path.basename(file_path)
            print(f"DEBUG: Uploading file {i+1}/{total_files_count}: {file_path} (Size: {format_bytes(file_size)})")

            if file_size > 2 * 1024 * 1024 * 1024:
                error_txt = f"❌ حجم الملف `{file_name_display}` ({format_bytes(file_size)}) يتجاوز حد تيليجرام (2GB)."
                try: await client.send_message(message.chat.id, error_txt)
                except Exception as send_err: print(f"Error sending size limit message: {send_err}")
                upload_errors.append(error_txt)
                try: os.remove(file_path)
                except OSError as e: print(f"Error removing large file {file_path}: {e}")
                continue

            # --- Prepare Metadata ---
            thumb_path = None; duration = 0; width = 0; height = 0
            try:
                import ffmpeg
                try:
                    print(f"DEBUG: Probing file for metadata: {file_path}")
                    probe = ffmpeg.probe(file_path)
                    format_info = probe.get('format', {})
                    duration = int(float(format_info.get('duration', 0)))

                    stream_info = next((s for s in probe['streams'] if s['codec_type'] == ('video' if media_type == 'video' else 'audio')), None)
                    if stream_info:
                         if media_type == 'video':
                             width = int(stream_info.get('width', 0))
                             height = int(stream_info.get('height', 0))
                             duration = int(float(stream_info.get('duration', format_info.get('duration',0)))) # Prefer stream duration for video
                             thumb_path = f"{os.path.splitext(file_path)[0]}_thumb.jpg"
                             try:
                                 (ffmpeg.input(file_path, ss=duration * 0.1 if duration > 1 else 0.1)
                                  .output(thumb_path, vframes=1, loglevel="error").overwrite_output()
                                  .run(capture_stdout=True, capture_stderr=True))
                                 if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0: thumb_path = None
                                 else: print(f"DEBUG: ffmpeg thumbnail generated: {thumb_path}")
                             except ffmpeg.Error as ff_err: print(f"WARN: ffmpeg thumbnail fail: {ff_err.stderr.decode()}"); thumb_path = None
                         elif media_type == 'audio':
                              duration = int(float(format_info.get('duration', stream_info.get('duration', 0))))

                except ffmpeg.Error as ff_err: print(f"WARN: ffprobe error: {ff_err.stderr.decode()}")
                except Exception as meta_err: print(f"WARN: Metadata extraction error: {meta_err}")

            except ImportError: print("WARN: ffmpeg-python not installed. Using basic metadata.")

            # Fallback metadata if ffmpeg failed/not installed
            stored_info = session_data.get('info_dict', {})
            if duration == 0 and stored_info.get('duration'): duration = int(stored_info['duration'])
            if media_type == 'video':
                if width == 0 and stored_info.get('width'): width = int(stored_info['width'])
                if height == 0 and stored_info.get('height'): height = int(stored_info['height'])

            # --- Prepare Caption ---
            current_title = session_data.get('final_title', 'محتوى يوتيوب')
            current_description = session_data.get('final_description', '')
            playlist_caption_part = f"\nالجزء {i+1}/{total_files_count}" if total_files_count > 1 else ""
            caption = f"**{current_title}{playlist_caption_part}**\n\n"
            if current_description and not session_data.get('is_playlist', False):
                 caption += f"{current_description[:200]}{'...' if len(current_description) > 200 else ''}\n\n"
            caption += f"تم التحميل بواسطة @{client.me.username}"
            caption = caption[:1020]

            # --- Send File ---
            reply_to_id = message.reply_to_message.id if message.reply_to_message else message.id
            try:
                 if media_type == 'video':
                     await client.send_video(
                         message.chat.id, video=file_path, caption=caption, thumb=thumb_path,
                         duration=duration, width=width, height=height,
                         progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count),
                         reply_to_message_id=reply_to_id )
                 elif media_type == 'audio':
                     extracted_title = os.path.splitext(file_name_display)[0][:60]
                     performer = stored_info.get('uploader', 'Unknown')[:60] if stored_info else 'Unknown'
                     await client.send_audio(
                         message.chat.id, audio=file_path, caption=caption, title=extracted_title, performer=performer,
                         thumb=thumb_path, duration=duration,
                         progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count),
                         reply_to_message_id=reply_to_id )
            except FloodWait as fw:
                 print(f"FloodWait: Waiting {fw.value}s...")
                 await asyncio.sleep(fw.value + 1)
                 # Retry logic simplified: just try again once
                 try:
                     if media_type == 'video': await client.send_video(message.chat.id, video=file_path, caption=caption, thumb=thumb_path, duration=duration, width=width, height=height, progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count), reply_to_message_id=reply_to_id)
                     else: await client.send_audio(message.chat.id, audio=file_path, caption=caption, title=extracted_title, performer=performer, thumb=thumb_path, duration=duration, progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count), reply_to_message_id=reply_to_id)
                 except Exception as retry_err:
                      print(f"ERROR: Upload retry failed: {retry_err}")
                      upload_errors.append(f"فشل إرسال `{file_name_display}`.")
            except Exception as upload_err:
                print(f"ERROR: Failed to send as Video/Audio: {upload_err}")
                upload_errors.append(f"فشل إرسال `{file_name_display}` كملف وسائط.")
                try: # Fallback to document
                    await client.send_document(
                        message.chat.id, document=file_path, caption=caption, thumb=thumb_path,
                        progress=upload_progress_callback, progress_args=(message, user_id, file_path, i + 1, total_files_count),
                        reply_to_message_id=reply_to_id )
                except Exception as doc_err:
                    print(f"ERROR: Failed to send as Document: {doc_err}")
                    upload_errors.append(f"فشل إرسال `{file_name_display}` كمستند أيضًا.")
            finally: # Cleanup regardless of success/failure
                 if os.path.exists(file_path):
                     try: os.remove(file_path); print(f"DEBUG: Removed file: {file_path}")
                     except OSError as e: print(f"Error removing file {file_path}: {e}")
                 if thumb_path and os.path.exists(thumb_path):
                     try: os.remove(thumb_path); print(f"DEBUG: Removed thumbnail: {thumb_path}")
                     except OSError as e: print(f"Error removing thumbnail {thumb_path}: {e}")

        # --- Final Status ---
        final_status_text = ""
        if upload_errors:
            final_status_text = "⚠️ اكتملت العملية مع الأخطاء التالية:\n" + "\n".join(upload_errors)
        else:
            final_status_text = f"✅ تم رفع جميع الملفات ({total_files_count}) بنجاح!"

        try:
            # Try to edit the status message first
            await message.edit_text(final_status_text)
            # Optionally delete after a delay
            await asyncio.sleep(15)
            await message.delete()
        except (MessageIdInvalid, MessageNotModified): # Message might be gone or unchanged
            print("WARN: Final status message was gone or unchanged.")
            # Send as new message if editing failed
            try: await client.send_message(message.chat.id, final_status_text, reply_to_message_id=reply_to_id)
            except Exception as final_send_err: print(f"Error sending final status as new message: {final_send_err}")
        except Exception as e:
            print(f"Error editing/deleting final status message: {e}")
            try: await client.send_message(message.chat.id, final_status_text, reply_to_message_id=reply_to_id)
            except Exception as final_send_err: print(f"Error sending final status as new message: {final_send_err}")

        # Clean up session
        if user_id in download_sessions:
            del download_sessions[user_id]

    # Acknowledge other button presses silently if not handled above
    try: await callback_query.answer()
    except: pass


# --- دالة عرض تقدم الرفع ---
async def upload_progress_callback(current, total, message, user_id, file_path, file_index, total_files):
    """Updates the message with upload progress."""
    session_data = download_sessions.get(user_id)
    status_message_id = session_data.get('status_message_id') if session_data else None
    if not session_data or not status_message_id: return

    now = time.time()
    last_update = session_data.get('last_upload_update_time', 0)
    if now - last_update < 1.5: return # Throttle

    session_data['last_upload_update_time'] = now

    try:
        percentage = current / total if total > 0 else 0
        progress_bar_str = progress_bar_generator(percentage)
        file_name_display = os.path.basename(file_path)
        current_size_str = format_bytes(current)
        total_size_str = format_bytes(total)
        playlist_info = f" (ملف {file_index}/{total_files})" if total_files > 1 else ""

        progress_text = (
            f"{session_data.get('initial_text', '✅ تم التحميل.')}\n\n"
            f"**⬆️ جاري الرفع{playlist_info}:**\n"
            f"`{file_name_display[:50]}{'...' if len(file_name_display)>50 else ''}`\n"
            f" {progress_bar_str} ({percentage*100:.1f}%)\n"
            f" {current_size_str} / {total_size_str}"
        )

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message_id,
            text=progress_text
        )
    except MessageNotModified: pass
    except FloodWait as fw:
        print(f"FloodWait in upload_progress: Waiting {fw.value}s...")
        await asyncio.sleep(fw.value + 1)
    except MessageIdInvalid:
        print(f"WARN: Upload progress - Message ID {status_message_id} invalid.")
        if user_id in download_sessions: download_sessions[user_id]['status_message_id'] = None
    except Exception as e:
        print(f"ERROR in upload_progress_callback: {type(e).__name__}: {e}")
        if user_id in download_sessions: download_sessions[user_id]['status_message_id'] = None


# --- تشغيل البوت ---
if __name__ == "__main__":
    print("البوت قيد التشغيل...")
    try:
        bot.run()
    except Exception as e:
        print(f"حدث خطأ فادح عند تشغيل البوت: {e}")
    finally:
        print("تم إيقاف البوت.")
