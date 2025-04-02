# language_handler.py

from database import digital_botz  # استيراد قاعدة البيانات

TEXTS = { # ... (قاموس TEXTS كما هو في الكود الأصلي) ...
"en": {
"start_message": "👋 Hi {mention}, I am a bot I can download restricted content from channels or groups I am a member of. To add a thumbnail for videos Talk to the owner.\n\n{usage}",
"start_usage_pro": """
Available commands:

/start: Start the bot.
/cancel: Stop current download or upload.
/status: Bot status.
/language: Change language.
""",
"start_usage_admin": """
Available commands:

/start: Start the bot.
/cancel: Stop current download or upload.
/restart: Restart the bot (admin command).
/status: Bot status.
/add_pro <user_id> <duration>: Add pro membership (admin command).
/remove_pro <user_id>: Remove pro membership (admin command).
/remove_thumb: Reset thumbnail to default (for your profile).
/set_thumb <user_id>: Set thumbnail for a user (admin command). Send photo after command.
/remove_thumb_user <user_id>: Reset user's thumbnail to default (admin command).
/language: Change language.
""",
"not_admin_message": "Sorry, you are not an admin or pro user. You cannot use this bot. Contact the owner: @X_XF8",
"not_admin_command_message": "Sorry, you are not an admin. You cannot use this command.",
"cancel_download": "Download stopped.",
"cancel_upload": "Upload stopped.",
"restarting": "Restarting bot...",
"status_title": "Bot Status:",
"status_uptime": "- Uptime: {}",
"status_active_admins": "- Active Admins: {}",
"status_bot_state": "- Bot State: {}",
"status_current_link": "- Current Link: {}",
"status_pro_users": "- Pro Users: {}",
"status_task_running": "Working on a task",
"status_idle": "Idle",
"add_pro_usage": "Incorrect usage!\nUse: /add_pro <user_id> <duration>\nExample: /add_pro 123456789 7days",
"invalid_duration": "Invalid duration!\nUse: hours, days, weeks, months, years",
"pro_added_user": "Thank you for purchasing premium membership!\n\nPurchase Date: {}\nExpiry Date: {}\n\nEnjoy using the bot!",
"pro_added_admin": "Pro membership added for user:\n\n- User ID: {}\n- Expiry Date: {}",
"remove_pro_usage": "Incorrect usage!\nUse: /remove_pro <user_id>",
"pro_removed_user": "Pro membership removed for user:\n\n- User ID: {}",
"thumb_reset_default": "Thumbnail reset to default.",
"set_thumb_usage": "Incorrect usage!\nUse: /set_thumb <user_id>",
"send_thumb_prompt": "Now send the photo you want to set as thumbnail for user ID: {}.",
"thumb_user_reset_default": "Thumbnail for user ID: {} reset to default.",
"user_id_invalid": "User ID must be a number.",
"error_occurred": "An error occurred: {}",
"daily_limit_reached": "You have reached your daily limit of {} tasks.\n\nTo continue using the bot, please upgrade to premium.\n\nContact @X_XF8 to upgrade.",
"download_started": "DOWNLOAD STARTED....\n\n{}\nBY: {}\nFILE SIZE: {:.2f} MB\nSPEED: N/A\n\nPROGRESS: 0%",
"upload_started": "UPLOAD STARTED....\n\n{}\nBY: {}\nFILE SIZE: {:.2f} MB\nSPEED: N/A\n\nPROGRESS: 0%",
"download_stopped": "Download stopped.",
"bulk_download_stopped": "Bulk download stopped.",
"bulk_download_completed": "Bulk Download Completed.",
"error_download_failed_retries": "Error : Download failed after multiple retries.\n__{}",
"error_unable_retrieve_message": "Error: Unable to retrieve the message.",
"error_download_failed_message_bulk": "Error : Download failed for message {} after multiple retries.\n{}__",
"error_bulk_processing": "Error in bulk link processing for msgid: {}, error: {}",
"error_generic": "Error : {}",
"user_not_found": "User ID: {} not found.",
"thumb_set_success_user": "Thumbnail for user ID: {} set successfully!",
"error_setting_thumb": "An error occurred while setting the thumbnail: {}",
"thumb_auto_set_admin": "Admin thumbnail set automatically!",
"language_select": "Please select your language:",
"language_changed": "Language changed to {lang_name}.", # Corrected placeholder
"change_language_button": "🌐 Change Language",
"owner_button": "🌐 OWNER",
"subscribe_message": "Please subscribe to our channel to use this bot:",
"subscribe_button": "Subscribe Now",
"first_start_message": "New user started the bot for the first time!",
"user_info_message": """ # Corrected placeholders to keyword args

Name: {user_first_name} {user_last_name}

Username: {user_username}

User ID: {user_id}

Entry Time: {entry_time}
""",
"choice_public_link": "Public Link Options:\n\n1. Send Media Now\n2. Download & Upload (Better Speed)",
"choice_send_now": "Send Now",
"choice_download_upload": "Download & Upload",
"choice_timeout": "No choice made in 3 seconds, sending media directly.",
},
"ar": { # ... (Arabic texts - no changes needed here)
"start_message": "👋 مرحبًا {mention}، أنا بوت يمكنني تنزيل المحتوى المقيد من القنوات أو المجموعات التي أنا عضو فيها. لإضافة صورة مصغرة للفيديوهات تحدث إلى المالك.\n\n{usage}",
"start_usage_pro": """
الأوامر المتاحة:

/start: بدء استخدام البوت.
/cancel: إيقاف التحميل أو الرفع الجاري.
/status: حالة البوت.
/language: تغيير اللغة.
""",
"start_usage_admin": """
الأوامر المتاحة:

/start: بدء استخدام البوت.
/cancel: إيقاف التحميل أو الرفع الجاري.
/restart: إعادة تشغيل البوت (أمر مسؤول).
/status: حالة البوت.
/add_pro <user_id> <مدة>: إضافة عضوية مميزة لمستخدم (أمر مسؤول).
/remove_pro <user_id>: إزالة العضوية المميزة من مستخدم (أمر مسؤول).
/remove_thumb: إعادة تعيين الصورة المصغرة إلى الافتراضية (لصورتك الشخصية).
/set_thumb <user_id>: تعيين صورة مصغرة لمستخدم معين (أمر مسؤول). أرسل الصورة بعد الأمر.
/remove_thumb_user <user_id>: إزالة الصورة المصغرة لمستخدم معين وإعادتها للافتراضية (أمر مسؤول).
/language: تغيير اللغة.
""",
"not_admin_message": "عذرًا، أنت لست الأدمن أو مستخدم مميز. لا يمكنك استخدام هذا البوت. تحدث إلى المالك: @X_XF8",
"not_admin_command_message": "عذرًا، أنت لست الأدمن. لا يمكنك استخدام هذا الأمر.",
"cancel_download": "تم إيقاف التحميل.",
"cancel_upload": "تم إيقاف الرفع.",
"restarting": "جارٍ إعادة تشغيل البوت...",
"status_title": "حالة البوت:",
"status_uptime": "- مدة التشغيل: {}",
"status_active_admins": "- عدد الأدمن النشطين: {}",
"status_bot_state": "- حالة البوت: {}",
"status_current_link": "- الرابط الحالي: {}",
"status_pro_users": "- عدد الأعضاء المميزين: {}",
"status_task_running": "يعمل على مهمة",
"status_idle": "خامل",
"add_pro_usage": "استخدام خاطئ!\nاستخدم: /add_pro <user_id> <مدة>\nمثال: /add_pro 123456789 7days",
"invalid_duration": "مدة غير صالحة!\nاستخدم: hours, days, weeks, months, years",
"pro_added_user": "شكرًا لشرائك العضوية المميزة!\n\nتاريخ الشراء: {}\nتاريخ انتهاء العضوية: {}\n\nاستمتع باستخدام البوت!",
"pro_added_admin": "تمت إضافة العضوية المميزة للمستخدم:\n\n- الـ ID: {}\n- تاريخ انتهاء العضوية: {}",
"remove_pro_usage": "استخدام خاطئ!\nاستخدم: /remove_pro <user_id>",
"pro_removed_user": "تمت إزالة العضوية المميزة للمستخدم:\n\n- الـ ID: {}",
"thumb_reset_default": "تمت إعادة تعيين الصورة المصغرة إلى الافتراضية.",
"set_thumb_usage": "استخدام خاطئ!\nاستخدم: /set_thumb <user_id>",
"send_thumb_prompt": "أرسل الآن الصورة التي تريد تعيينها كصورة مصغرة للمستخدم ID: {}.",
"thumb_user_reset_default": "تمت إعادة تعيين الصورة المصغرة للمستخدم ID: {} إلى الصورة الافتراضية.",
"user_id_invalid": "معرف المستخدم يجب أن يكون رقمًا.",
"error_occurred": "حدث خطأ: {}",
"daily_limit_reached": "لقد وصلت إلى الحد اليومي المسموح به وهو {} مهمة.\n\nللاستمرار في استخدام البوت، يرجى الترقية إلى العضوية المميزة.\n\nتواصل مع @X_XF8 للترقية.",
"download_started": "بدء التحميل....\n\n{}\nبواسطة: {}\nحجم الملف: {:.2f} ميجابايت\nالسرعة: غير متاحة\n\nالتقدم: 0%",
"upload_started": "بدء الرفع....\n\n{}\nبواسطة: {}\nحجم الملف: {:.2f} ميجابايت\nالسرعة: غير متاحة\n\nالتقدم: 0%",
"download_stopped": "تم إيقاف التحميل.",
"bulk_download_stopped": "تم إيقاف التحميل الجماعي.",
"bulk_download_completed": "اكتمل التحميل الجماعي.",
"error_download_failed_retries": "خطأ: فشل التحميل بعد عدة محاولات.\n__{}",
"error_unable_retrieve_message": "خطأ: تعذر استرداد الرسالة.",
"error_download_failed_message_bulk": "خطأ: فشل تحميل الرسالة {} بعد عدة محاولات.\n{}__",
"error_bulk_processing": "خطأ في معالجة الرابط المجمع للرسالة: {}، الخطأ: {}",
"error_generic": "خطأ: {}",
"user_not_found": "المستخدم ID: {} غير موجود.",
"thumb_set_success_user": "تم تعيين الصورة المصغرة للمستخدم ID: {} بنجاح!",
"error_setting_thumb": "حدث خطأ أثناء تعيين الصورة المصغرة: {}",
"thumb_auto_set_admin": "تم تعيين الصورة المصغرة للمسؤول تلقائيًا!",
"language_select": "الرجاء اختيار لغتك:",
"language_changed": "تم تغيير اللغة إلى {lang_name}.", # Corrected placeholder
"change_language_button": "🌐 تغيير اللغة",
"owner_button": "🌐 المالك",
"subscribe_message": "يرجى الاشتراك في قناتنا لاستخدام هذا البوت:",
"subscribe_button": "اشترك الآن",
"first_start_message": "مستخدم جديد بدأ البوت لأول مرة!",
"user_info_message": """ # Corrected placeholders to keyword args

الاسم: {user_first_name} {user_last_name}

اليوزر: {user_username}

الـ ID: {user_id}

وقت وتاريخ الدخول: {entry_time}
""",
"choice_public_link": "خيارات الرابط العام:\n\n1. إرسال الوسائط الآن\n2. تنزيل وتحميل (سرعة أفضل)",
"choice_send_now": "ارسل الان",
"choice_download_upload": "تنزيل وتحميل",
"choice_timeout": "لم يتم الاختيار خلال 3 ثوانٍ، سيتم إرسال الوسائط مباشرة.",
}
}

def get_text(key, lang="en", **kwargs):
    """Get localized text."""
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"][key]).format(**kwargs)

async def set_user_language(user_id, lang):
    await digital_botz.set_user_language(user_id, lang) # Use database function

async def get_user_language(user_id):
    lang_code = await digital_botz.get_user_language(user_id) # Use database function
    return lang_code if lang_code else "en" # Default to English if not in DB