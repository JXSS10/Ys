import os
import re
import yt_dlp
import http.cookiejar
from io import StringIO

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified

# تهيئة المتغيرات البيئية (API IDs, Tokens)
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# بيانات البوت
if not API_ID or not API_HASH or not BOT_TOKEN:
    print("يرجى التأكد من تعيين متغيرات API_ID و API_HASH و BOT_TOKEN البيئية.")
    exit()

bot = Client(
    "URL_UPLOADER_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# مجلد التحميل
DOWNLOAD_FOLDER = "./downloads"  # تم تغيير الاسم ليكون أكثر وصفاً
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# قاموس لتخزين بيانات التنزيل المؤقتة لكل مستخدم
download_sessions = {}

# كوكيز يوتيوب (تم تضمينها مباشرة كمتغير نصي)
YTUB_COOKIES = """
Netscape HTTP Cookie File
# This is a generated file!  Do not edit.
... (محتوى الكوكيز كما هو في الكود الأصلي) ...
"""

# دالة تنزيل محتوى يوتيوب (فيديو أو صوت)
def download_youtube_content(url, message, format_id, user_id, media_type):
    """
    يقوم بتنزيل محتوى يوتيوب (فيديو أو صوت) باستخدام yt-dlp.

    Args:
        url (str): رابط يوتيوب.
        message (pyrogram.types.Message): رسالة المستخدم لبدء التنزيل.
        format_id (str): مُعرّف الصيغة المراد تنزيلها.
        user_id (int): مُعرّف المستخدم الذي طلب التنزيل.
        media_type (str): نوع الوسائط ('video' أو 'audio').

    Returns:
        tuple: قائمة بأسماء الملفات التي تم تنزيلها وعنوان الفيديو، أو (None, رسالة خطأ) في حالة الفشل.
    """
    print(f"DEBUG: DOWNLOAD_FOLDER is: {DOWNLOAD_FOLDER}")

    # تحميل الكوكيز من المتغير النصي
    cookie_jar = http.cookiejar.MozillaCookieJar()
    try:
        cookie_jar.load(StringIO(YTUB_COOKIES), ignore_discard=True, ignore_expires=True)
        print("DEBUG: Cookies loaded from variable.")
    except Exception as e:
        print(f"DEBUG: Error loading cookies from variable: {e}")
        cookie_jar = None  # عدم استخدام الكوكيز في حالة الفشل

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'progress_hooks': [lambda d: progress_hook(d, message, user_id, "download")],
        'format': format_id,
        'cookiejar': cookie_jar,
        'verbose': True,  # تفعيل الإخراج المطول للمزيد من معلومات التصحيح
        'http_headers': {  # تحسين محاكاة المتصفح
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', # تحسين Accept header
            'Accept-Language': 'en-US,en;q=0.9', # تحسين Accept-Language header
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        },
        'nocheckcertificate': True, # إضافة لتجاهل شهادات SSL إذا لزم الأمر (للتصحيح فقط، تجنب في الإنتاج إذا أمكن)
    }

    if media_type == 'audio':
        ydl_opts['extractaudio'] = True
        ydl_opts['no_video'] = True
        ydl_opts['format'] = 'bestaudio'  # تحميل أفضل جودة صوتية افتراضياً

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_files = [os.path.join(DOWNLOAD_FOLDER, ydl.prepare_filename(entry))
                           for entry in info_dict['entries']] if 'entries' in info_dict else \
                          [os.path.join(DOWNLOAD_FOLDER, ydl.prepare_filename(info_dict))]
            print(f"DEBUG: Downloaded files: {video_files}")
            return video_files, info_dict.get('title', 'محتوى يوتيوب')
    except Exception as e:
        print(f"DEBUG: Download Error: {e}")
        return None, str(e)

# دالة عرض التقدم (تم إعادة هيكلتها قليلاً للوضوح)
async def progress_hook(d, message, user_id, process_type):
    """
    دالة رد نداء يتم استدعاؤها بواسطة yt-dlp لتحديث حالة التقدم في رسالة تيليجرام.

    Args:
        d (dict): قاموس معلومات التقدم من yt-dlp.
        message (pyrogram.types.Message): رسالة التقدم ليتم تعديلها.
        user_id (int): مُعرّف المستخدم المرتبط بالعملية.
        process_type (str): نوع العملية ('download' أو 'upload').
    """
    if d['status'] in ('downloading', 'uploading'):
        percentage = d.get('_percent_str', '0.0%').strip('%')
        percentage = float(percentage) / 100 if percentage else 0.0
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        total_size = d.get('_total_bytes_str', 'N/A')
        current_size = d.get('_downloaded_bytes_str', 'N/A')

        progress_bar = progress_bar_generator(percentage)
        process_text = {
            "download": "جاري التحميل من يوتيوب",
            "upload": "جاري الرفع إلى تيليجرام"
        }.get(process_type, "جاري المعالجة")

        progress_text = (
            f"**{process_text}:**\n"
            f"📦 {progress_bar} ({percentage * 100:.1f}%)\n"
            f"⬇️ السرعة: {speed} | ⏳ المتبقي: {eta}\n"
            f"حجم الملف: {current_size} / {total_size}"
        )

        session_data = download_sessions.get(user_id)
        if session_data and session_data['status_message_id'] == message.id:
            try:
                await message.edit_text(f"{session_data['initial_text']}\n\n{progress_text}",
                                        reply_markup=session_data['reply_markup'])
            except MessageNotModified:
                pass
            except Exception as e:
                print(f"خطأ في تحديث رسالة التقدم: {e}")

# دالة إنشاء شريط التقدم المرئي (كما هي)
def progress_bar_generator(percentage, bar_length=20):
    """
    إنشاء شريط تقدم نصي بناءً على النسبة المئوية.

    Args:
        percentage (float): النسبة المئوية للتقدم (بين 0 و 1).
        bar_length (int): طول شريط التقدم النصي.

    Returns:
        str: شريط التقدم النصي.
    """
    completed_blocks = int(round(bar_length * percentage))
    remaining_blocks = bar_length - completed_blocks
    progress_bar = '█' * completed_blocks + '░' * remaining_blocks
    return progress_bar

# معالج أوامر البدء و المساعدة
@bot.on_message(filters.command(["start", "help"]))
async def start_command(client, message):
    """معالج لأوامر /start و /help."""
    await message.reply_text(
        "أهلاً بك! أنا بوت تحميل فيديوهات يوتيوب.\n"
        "أرسل لي رابط فيديو يوتيوب أو قائمة تشغيل وسأقوم بتحميلها وإرسالها لك.\n\n"
        "**طريقة الاستخدام:**\n"
        "أرسل رابط يوتيوب (فيديو أو قائمة تشغيل) في هذه الدردشة.\n\n"
        "**الصيغ المدعومة:**\n"
        "يدعم البوت صيغ 240p, 360p, 480p, 720p للفيديو وصيغ صوتية متعددة.\n\n"
        "**خيارات التحميل:**\n"
        "بعد إرسال الرابط، سيتم سؤالك إذا كنت تريد تحميل الفيديو أو الصوت، ثم سيتم عرض قائمة بالجودات المتاحة.\n\n"
        "**ملاحظات:**\n"
        "- قد يستغرق التحميل بعض الوقت حسب حجم الفيديو وسرعة الإنترنت.\n"
        "- إذا كان الفيديو كبيرًا جدًا، قد لا يتمكن تيليجرام من إرساله مباشرة.\n"
        "- إذا واجهت أي مشاكل، يمكنك التواصل مع مطور البوت."
    )

# دالة لجلب صيغ الفيديو المتاحة
def get_video_formats(url, media_type):
    """
    جلب صيغ الفيديو/الصوت المتاحة من يوتيوب باستخدام yt-dlp.

    Args:
        url (str): رابط يوتيوب.
        media_type (str): نوع الوسائط ('video' أو 'audio').

    Returns:
        list: قائمة بالصيغ المتاحة أو None في حالة حدوث خطأ.
    """
    ydl_opts = {
        'format': 'best',
        'listformats': True,
        'quiet': True,
        'verbose': True, # تفعيل الإخراج المطول للمزيد من معلومات التصحيح
        'http_headers': {  # تحسين محاكاة المتصفح
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', # تحسين Accept header
            'Accept-Language': 'en-US,en;q=0.9', # تحسين Accept-Language header
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        },
        'nocheckcertificate': True, # إضافة لتجاهل شهادات SSL إذا لزم الأمر (للتصحيح فقط، تجنب في الإنتاج إذا أمكن)
    }

    # تحميل الكوكيز من المتغير النصي
    cookie_jar = http.cookiejar.MozillaCookieJar()
    try:
        cookie_jar.load(StringIO(YTUB_COOKIES), ignore_discard=True, ignore_expires=True)
        print("DEBUG: Cookies loaded from variable for get_video_formats.")
        ydl_opts['cookiejar'] = cookie_jar
    except Exception as e:
        print(f"DEBUG: Error loading cookies from variable in get_video_formats: {e}")
        ydl_opts['cookiejar'] = None

    print(f"DEBUG: get_video_formats called for URL: {url}, media_type: {media_type}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            print(f"DEBUG: info_dict from yt-dlp: {info_dict}")
            formats = info_dict.get('formats', [])
            print(f"DEBUG: All formats from yt-dlp: {formats}")

            if media_type == 'video':
                filtered_formats = []
                resolutions = ["240p", "360p", "480p", "720p"]
                for f in formats:
                    format_note = f.get('format_note', '').lower()
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':  # التأكد من وجود فيديو وصوت
                        for res in resolutions:
                            if format_note.startswith(res):
                                filtered_formats.append(f)
                                break
                print(f"DEBUG: Filtered video formats: {filtered_formats}")
                return filtered_formats
            elif media_type == 'audio':
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                print(f"DEBUG: Filtered audio formats: {audio_formats}")
                return audio_formats
            else:
                return None  # نوع ميديا غير مدعوم

    except Exception as e:
        print(f"DEBUG: Error in get_video_formats: {e}")
        return None

# معالج الرسائل النصية (روابط يوتيوب)
@bot.on_message(filters.text)
async def handle_youtube_url(client, message):
    """
    معالج للرسائل النصية، يبحث عن روابط يوتيوب ويبدأ عملية التحميل.
    """
    url = message.text.strip()
    youtube_regex = re.compile(
        r'(https?://)?(www.)?(youtube|youtu|youtube-nocookie).(com|be)/(watch?v=|embed/|v/|shorts/|playlist?list=)?([\w-]{11,})([&|?].*)?'
    )

    if youtube_regex.match(url):
        try:
            # خيارات نوع الميديا (فيديو أو صوت)
            media_type_buttons = [
                [InlineKeyboardButton("فيديو 🎬", callback_data="type_video")],
                [InlineKeyboardButton("صوت 🔉", callback_data="type_audio")],
                [InlineKeyboardButton("إلغاء ❌", callback_data="type_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(media_type_buttons)
            initial_text = "اختر نوع التحميل:"
            status_message = await message.reply_text(initial_text, reply_markup=reply_markup)

            # حفظ معلومات الجلسة
            download_sessions[message.from_user.id] = {
                'status_message_id': status_message.id,
                'initial_text': initial_text,
                'reply_markup': reply_markup,
                'url': url,
                'media_type': None  # سيتم تحديده لاحقاً
            }

        except Exception as e:
            await message.reply_text(f"حدث خطأ:\n\n`{e}`")
    else:
        await message.reply_text("هذا ليس رابط يوتيوب صالحًا. يرجى إرسال رابط يوتيوب صحيح.")

# معالج استعلامات ردود الفعل
@bot.on_callback_query()
async def format_callback(client, callback_query: CallbackQuery):
    """
    معالج لاستعلامات ردود الفعل (اختيار نوع الميديا والصيغة).
    """
    user_id = callback_query.from_user.id
    session_data = download_sessions.get(user_id)

    if not session_data or callback_query.message.id != session_data['status_message_id']:
        return await callback_query.answer("انتهت صلاحية هذه الخيارات، يرجى إرسال الرابط مرة أخرى.")

    callback_data = callback_query.data

    if callback_data.startswith("type_"):  # معالجة اختيار نوع الميديا
        media_type = callback_data.replace("type_", "")
        if media_type == "cancel":
            await callback_query.message.edit_text("تم إلغاء التحميل.")
            download_sessions.pop(user_id, None)
            return await callback_query.answer()

        session_data['media_type'] = media_type

        await callback_query.message.edit_text(f"تم اختيار **{media_type.capitalize()}**.\nجاري جلب الجودات المتاحة...",
                                                reply_markup=None)

        formats = get_video_formats(session_data['url'], media_type)

        if not formats:
            return await callback_query.message.edit_text(f"لم يتم العثور على صيغ متاحة لـ **{media_type}**.")

        buttons = []
        unique_formats = {}

        if media_type == 'video':
            resolutions = ["240p", "360p", "480p", "720p"]
            for res in resolutions:
                for f in formats:
                    format_str = f"{f.get('format_note', 'صيغة غير محددة')}"
                    if format_str.lower().startswith(res):
                        format_id = f['format_id']
                        if format_str not in unique_formats:
                            unique_formats[format_str] = format_id
                            format_display = f"{format_str} ({f.get('ext', '').upper()})" if f.get('ext') == 'mp4' else format_str
                            buttons.append([InlineKeyboardButton(format_display, callback_data=f"format_{format_id}")])
            initial_text = "اختر جودة الفيديو المطلوبة (MP4):"

        elif media_type == 'audio':
            for f in formats:
                format_str = f"{f.get('format_note', 'صيغة غير محددة')} - {f.get('acodec', 'بدون ترميز')} ({f.get('abr', 'غير محدد')} kbps)"
                format_id = f['format_id']
                if format_str not in unique_formats:
                    unique_formats[format_str] = format_id
                    buttons.append([InlineKeyboardButton(format_str, callback_data=f"format_{format_id}")])
            initial_text = "اختر جودة الصوت المطلوبة:"

        buttons.append([InlineKeyboardButton("إلغاء", callback_data="format_cancel")])

        if not buttons:
            return await callback_query.message.edit_text(f"لا توجد صيغ متاحة للعرض لـ **{media_type}**.")

        reply_markup = InlineKeyboardMarkup(buttons)
        session_data['reply_markup'] = reply_markup
        session_data['initial_text'] = initial_text
        await callback_query.message.edit_text(initial_text, reply_markup=reply_markup)
        return await callback_query.answer()

    if callback_data.startswith("format_"):  # معالجة اختيار الصيغة
        format_option = callback_data.replace("format_", "")

        if format_option == "cancel":
            await callback_query.message.edit_text("تم إلغاء التحميل.")
            download_sessions.pop(user_id, None)
            return await callback_query.answer()

        await callback_query.message.edit_text(f"جاري التحضير للتحميل بالصيغة المختارة...\n\n{session_data['initial_text']}",
                                                reply_markup=None)
        await callback_query.answer("بدء التحميل...")

        url = session_data['url']
        status_message = callback_query.message
        media_type = session_data['media_type']
        video_files, error_message = download_youtube_content(url, status_message, format_option, user_id, media_type)
        session_data['video_files'] = video_files

        if video_files:
            await status_message.edit_text(f"تم التحميل بنجاح! جاري إرسال الملف/الملفات...\n\n{session_data['initial_text']}")
            for video_file in video_files:
                if os.path.exists(video_file):
                    try:
                        if media_type == 'video':
                            await bot.send_video(
                                chat_id=callback_query.message.chat.id,
                                video=video_file,
                                caption=f"تم التحميل بواسطة @{bot.me.username}",
                                progress=upload_progress_callback,
                                progress_args=(status_message, user_id, video_file, len(video_files))
                            )
                        elif media_type == 'audio':
                            await bot.send_audio(
                                chat_id=callback_query.message.chat.id,
                                audio=video_file,
                                caption=f"تم التحميل بواسطة @{bot.me.username}",
                                progress=upload_progress_callback,
                                progress_args=(status_message, user_id, video_file, len(video_files))
                            )
                    except Exception:  # استخدام Exception بدلاً من BaseException
                        await bot.send_document(
                            chat_id=callback_query.message.chat.id,
                            document=video_file,
                            caption=f"تم التحميل بواسطة @{bot.me.username}",
                            progress=upload_progress_callback,
                            progress_args=(status_message, user_id, video_file, len(video_files))
                        )
                    os.remove(video_file)
                else:
                    await status_message.reply_text(f"خطأ: الملف `{video_file}` غير موجود بعد التنزيل.")
            await status_message.delete()
            download_sessions.pop(user_id, None)
        else:
            await status_message.edit_text(f"حدث خطأ أثناء التنزيل:\n\n`{error_message}`")
        return await callback_query.answer()

    await callback_query.answer()  # رد افتراضي لأي استعلامات رد فعل أخرى

# دالة عرض تقدم الرفع
async def upload_progress_callback(current, total, status_message, user_id, video_file, total_files):
    """
    دالة رد نداء يتم استدعاؤها أثناء رفع الملف لتحديث حالة التقدم.

    Args:
        current (int): مقدار البيانات التي تم رفعها حتى الآن.
        total (int): الحجم الكلي للملف.
        status_message (pyrogram.types.Message): رسالة التقدم ليتم تعديلها.
        user_id (int): مُعرّف المستخدم المرتبط بالعملية.
        video_file (str): مسار الملف الذي يتم رفعه.
        total_files (int): العدد الكلي للملفات التي سيتم رفعها (في حالة قوائم التشغيل).
    """
    percentage = current / total
    session_data = download_sessions.get(user_id)
    if session_data and session_data['status_message_id'] == status_message.id:
        file_name = os.path.basename(video_file)
        file_index = session_data['video_files'].index(video_file) + 1 if 'video_files' in session_data and video_file in session_data['video_files'] else '?'
        process_text = ""
        if session_data['media_type'] == 'video':
            process_text = f"جاري الرفع إلى تيليجرام (الفيديو {file_index} من {total_files})"
        elif session_data['media_type'] == 'audio':
            process_text = f"جاري الرفع إلى تيليجرام (الصوت {file_index} من {total_files})"

        progress_text = (
            f"{process_text}:\n"
            f"📦 {progress_bar_generator(percentage)} ({percentage * 100:.1f}%)\n"
            f"اسم الملف: {file_name}"
        )
        try:
            await status_message.edit_text(f"{session_data['initial_text']}\n\n{progress_text}",
                                            reply_markup=session_data['reply_markup'])
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"خطأ في تحديث رسالة رفع التقدم: {e}")

# تشغيل البوت
if __name__ == "__main__":
    print("البوت يعمل...")
    bot.run()
