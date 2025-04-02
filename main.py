import os
import re
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
import http.cookiejar
from io import StringIO

API_ID = os.environ.get("API_ID", )
API_HASH = os.environ.get("API_HASH","")
BOT_TOKEN = os.environ.get("BOT_TOKEN","")

--- بيانات البوت ---

bot = Client(
"URL UPLOADER BOT",
api_id=API_ID,  # هام: استبدل بـ API ID الخاص بك
api_hash=API_HASH, # هام: استبدل بـ API HASH الخاص بك
bot_token=BOT_TOKEN # هام: استبدل بـ BOT TOKEN الخاص بك
)

--- مجلد التحميل ---

DOWNLOAD_FOLDER = "./"
if not os.path.exists(DOWNLOAD_FOLDER):
os.makedirs(DOWNLOAD_FOLDER)

--- قاموس لتخزين بيانات التنزيل المؤقتة ---

download_sessions = {}

--- ملف الكوكيز ---

YTUB_COOKIES = """
Netscape HTTP Cookie File

This is a generated file!  Do not edit.

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

#COOKIES_FILE = "cookies.txt"  # اسم ملف الكوكيز المؤقت - لم نعد نستخدم الملف

--- دالة لحفظ الكوكيز في ملف مؤقت ---

#def save_cookies_to_file(): # لم نعد نستخدم هذه الدالة

try:
with open(COOKIES_FILE, 'w') as f:
f.write(YTUB_COOKIES)
print("DEBUG: Cookies saved to file.")
print("DEBUG: Cookies file content:\n", YTUB_COOKIES) # Print content for verification
except Exception as e:
print(f"DEBUG: Error saving cookies to file: {e}")
--- دالة تنزيل الفيديو/قائمة التشغيل (معدلة لدعم نوع الميديا والكوكيز) ---

def download_youtube_content(url, message, format_id, user_id, media_type):
print(f"DEBUG: DOWNLOAD_FOLDER is: {DOWNLOAD_FOLDER}")
#save_cookies_to_file()  # حفظ الكوكيز قبل كل تنزيل - لم نعد نستخدم هذه الدالة

تحميل الكوكيز مباشرة من المتغير

cookie_jar = http.cookiejar.MozillaCookieJar()
try:
cookie_jar.load(StringIO(YTUB_COOKIES), ignore_discard=True, ignore_expires=True)
print("DEBUG: Cookies loaded from variable.")
except Exception as e:
print(f"DEBUG: Error loading cookies from variable: {e}")
cookie_jar = None  # في حالة فشل التحميل، لا تستخدم الكوكيز

ydl_opts = {
'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
'progress_hooks': [lambda d: progress_hook(d, message, user_id, "download")],
'format': format_id,
#'cookiefile': COOKIES_FILE,  # استخدام ملف الكوكيز - لم نعد نستخدم الملف
'cookiejar': cookie_jar, # استخدام cookiejar object
'verbose': True, # تفعيل الإخراج المطول لـ yt-dlp للمزيد من معلومات التصحيح
'http_headers': { # تعديل محتمل: إضافة هيدرات إضافية لمحاكاة المتصفح
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
'Accept-Language': 'en-us,en;q=0.5',
'Sec-Fetch-Mode': 'navigate'
}
}

if media_type == 'audio':
ydl_opts['extractaudio'] = True
ydl_opts['no_video'] = True
ydl_opts['format'] = 'bestaudio'  # تحميل أفضل جودة صوتية افتراضياً

try:
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
info_dict = ydl.extract_info(url, download=True)
if 'entries' in info_dict:
video_files = [os.path.join(DOWNLOAD_FOLDER, ydl.prepare_filename(entry)) for entry in info_dict['entries']]
else:
video_files = [os.path.join(DOWNLOAD_FOLDER, ydl.prepare_filename(info_dict))]
print(f"DEBUG: Downloaded files: {video_files}")
return video_files, info_dict.get('title', 'محتوى يوتيوب')
except Exception as e:
print(f"DEBUG: Download Error: {e}")
return None, str(e)

--- دالة عرض التقدم (كما هي) ---

async def progress_hook(d, message, user_id, process_type):

... (باقي الكود لدالة progress_hook كما هو في الكود السابق)

if d['status'] == 'downloading' or d['status'] == 'uploading':
percentage = float(d['_percent_str'].strip('%')) / 100 if '_percent_str' in d else 0.0
speed = d['_speed_str'] if '_speed_str' in d else "N/A"
eta = d['_eta_str'] if '_eta_str' in d else "N/A"
total_size = d['_total_bytes_str'] if '_total_bytes_str' in d else "N/A"
current_size = d['_downloaded_bytes_str'] if '_downloaded_bytes_str' in d else "N/A"

progress_bar = progress_bar_generator(percentage)

if process_type == "download":
    process_text = "جاري التحميل من يوتيوب"
elif process_type == "upload":
    process_text = "جاري الرفع إلى تيليجرام"
else:
    process_text = "جاري المعالجة"

progress_text = (
    f"**{process_text}:**\n"
    f"📦 {progress_bar} ({percentage*100:.1f}%)\n"
    f"⬇️ السرعة: {speed} | ⏳ المتبقي: {eta}\n"
    f"حجم الملف: {current_size} / {total_size}"
)

session_data = download_sessions.get(user_id)
if session_data and session_data['status_message_id'] == message.id:
    try:
        await message.edit_text(f"{session_data['initial_text']}\n\n{progress_text}", reply_markup=session_data['reply_markup'])
    except MessageNotModified:
        pass
    except Exception as e:
        print(f"خطأ في تحديث رسالة التقدم: {e}")



--- دالة إنشاء شريط التقدم المرئي (كما هي) ---

def progress_bar_generator(percentage, bar_length=20):
completed_blocks = int(round(bar_length * percentage))
remaining_blocks = bar_length - completed_blocks
progress_bar = '█' * completed_blocks + '░' * remaining_blocks
return progress_bar

--- معالج أوامر البدء (كما هو) ---

@bot.on_message(filters.command(["start", "help"]))
async def start_command(client, message):

... (باقي الكود لدالة start_command كما هو في الكود السابق)

await message.reply_text(
"أهلاً بك! أنا بوت تحميل فيديوهات يوتيوب.\n"
"أرسل لي رابط فيديو يوتيوب أو قائمة تشغيل وسأقوم بتحميلها وإرسالها لك.\n\n"
"طريقة الاستخدام:\n"
"أرسل رابط يوتيوب (فيديو أو قائمة تشغيل) في هذه الدردشة.\n\n"
"الصيغ المدعومة:\n"
"يدعم البوت صيغ 240p, 360p, 480p, 720p للفيديو وصيغ صوتية متعددة.\n\n"
"خيارات التحميل:\n"
"بعد إرسال الرابط، سيتم سؤالك إذا كنت تريد تحميل الفيديو أو الصوت، ثم سيتم عرض قائمة بالجودات المتاحة.\n\n"
"ملاحظات:\n"
"- قد يستغرق التحميل بعض الوقت حسب حجم الفيديو وسرعة الإنترنت.\n"
"- إذا كان الفيديو كبيرًا جدًا، قد لا يتمكن تيليجرام من إرساله مباشرة.\n"
"- إذا واجهت أي مشاكل، يمكنك التواصل مع مطور البوت."
)

--- دالة لجلب صيغ الفيديو المتاحة (معدلة لدعم نوع الميديا وعرض MP4) ---

def get_video_formats(url, media_type):
ydl_opts = {
'format': 'best',
'listformats': True,
'quiet': True,
#'cookiefile': COOKIES_FILE,  # استخدام ملف الكوكيز هنا أيضًا - لم نعد نستخدم الملف
'verbose': True, # تفعيل الإخراج المطول لـ yt-dlp للمزيد من معلومات التصحيح
'http_headers': { # تعديل محتمل: إضافة هيدرات إضافية لمحاكاة المتصفح
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
'Accept-Language': 'en-us,en;q=0.5',
'Sec-Fetch-Mode': 'navigate'
}
}
#save_cookies_to_file()  # حفظ الكوكيز قبل جلب الصيغ - لم نعد نستخدم هذه الدالة

تحميل الكوكيز مباشرة من المتغير

cookie_jar = http.cookiejar.MozillaCookieJar()
try:
cookie_jar.load(StringIO(YTUB_COOKIES), ignore_discard=True, ignore_expires=True)
print("DEBUG: Cookies loaded from variable for get_video_formats.")
ydl_opts['cookiejar'] = cookie_jar # استخدام cookiejar object
except Exception as e:
print(f"DEBUG: Error loading cookies from variable in get_video_formats: {e}")
ydl_opts['cookiejar'] = None # في حالة فشل التحميل، لا تستخدم الكوكيز

print(f"DEBUG: get_video_formats called for URL: {url}, media_type: {media_type}") # طباعة عند استدعاء الدالة

try:
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
info_dict = ydl.extract_info(url, download=False)
print(f"DEBUG: info_dict from yt-dlp: {info_dict}")  # طباعة معلومات الاستخراج الكاملة
formats = info_dict.get('formats', [])
print(f"DEBUG: All formats from yt-dlp: {formats}")  # طباعة جميع الصيغ المستخرجة

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
        print(f"DEBUG: Filtered video formats: {filtered_formats}")  # طباعة الصيغ بعد تصفية الفيديو
        return filtered_formats
    elif media_type == 'audio':
        audio_formats = []
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # صيغ صوتية فقط
                audio_formats.append(f)
        print(f"DEBUG: Filtered audio formats: {audio_formats}")  # طباعة الصيغ بعد تصفية الصوت
        return audio_formats
    else:
        return None  # نوع ميديا غير مدعوم


except Exception as e:
print(f"DEBUG: Error in get_video_formats: {e}")
return None

--- معالج الرسائل النصية (روابط يوتيوب) - معدل لاختيار نوع الميديا أولاً ---

@bot.on_message(filters.text)
async def handle_youtube_url(client, message):

... (باقي الكود لدالة handle_youtube_url كما هو في الكود السابق)

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

# حفظ معلومات الجلسة (بدون الصيغ حتى الآن)
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

--- معالج استعلامات ردود الفعل (معدل لدعم نوع الميديا واختيار الصيغة) ---

@bot.on_callback_query()
async def format_callback(client, callback_query: CallbackQuery):

... (باقي الكود لدالة format_callback كما هو في الكود السابق)

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

session_data['media_type'] = media_type  # تحديث نوع الميديا في الجلسة

await callback_query.message.edit_text(f"تم اختيار **{media_type.capitalize()}**.\nجاري جلب الجودات المتاحة...", reply_markup=None)

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
                    # عرض صيغة MP4 بوضوح إذا كانت كذلك
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
session_data['reply_markup'] = reply_markup  # تحديث الردود في الجلسة
session_data['initial_text'] = initial_text  # تحديث النص الأولي في الجلسة
await callback_query.message.edit_text(initial_text, reply_markup=reply_markup)
return await callback_query.answer()  # منع معالجة 'format_' بالأسفل


if callback_data.startswith("format_"):  # معالجة اختيار الصيغة
format_option = callback_data.replace("format_", "")

if format_option == "cancel":
    await callback_query.message.edit_text("تم إلغاء التحميل.")
    download_sessions.pop(user_id, None)
    return await callback_query.answer()

await callback_query.message.edit_text(f"جاري التحضير للتحميل بالصيغة المختارة...\n\n{session_data['initial_text']}", reply_markup=None)
await callback_query.answer("بدء التحميل...")

url = session_data['url']
status_message = callback_query.message
media_type = session_data['media_type']  # استرجاع نوع الميديا من الجلسة
video_files, error_message = download_youtube_content(url, status_message, format_option, user_id, media_type)  # تمرير نوع الميديا إلى دالة التنزيل
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
            except:  # في حال فشل إرسال الفيديو/الصوت كملف وسائط، يتم إرساله كمستند
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
return await callback_query.answer()  # منع تكرار الإجابة


await callback_query.answer()  # إجابة افتراضية لأي استعلامات رد فعل أخرى

--- دالة عرض تقدم الرفع (كما هي) ---

async def upload_progress_callback(current, total, status_message, user_id, video_file, total_files):

... (باقي الكود لدالة upload_progress_callback كما هو في الكود السابق)

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
f"📦 {progress_bar_generator(percentage)} ({percentage*100:.1f}%)\n"
f"اسم الملف: {file_name}"
)
try:
await status_message.edit_text(f"{session_data['initial_text']}\n\n{progress_text}", reply_markup=session_data['reply_markup'])
except MessageNotModified:
pass
except Exception as e:
print(f"خطأ في تحديث رسالة رفع التقدم: {e}")

--- تشغيل البوت ---

if name == "main":
print("البوت يعمل...")



