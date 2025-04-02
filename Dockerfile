# استخدم صورة بايثون رسمية كنقطة انطلاق
# استخدام نسخة slim يقلل حجم الصورة النهائية
FROM python:3.9-slim-buster

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# تحديث قائمة الحزم وتثبيت FFmpeg و git (قد تحتاجه بعض مكتبات بايثون)
# --no-install-recommends يمنع تثبيت الحزم غير الضرورية
# يتم دمج الأوامر في طبقة واحدة لتقليل حجم الصورة وتنظيف الكاش بعد الانتهاء
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات أولاً للاستفادة من ذاكرة التخزين المؤقت لـ Docker
COPY requirements.txt /app/

# تثبيت مكتبات بايثون المطلوبة
# --no-cache-dir يقلل حجم الصورة عن طريق عدم تخزين الكاش الخاص بـ pip
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ باقي كود التطبيق إلى مجلد العمل
COPY . /app

# تحديد الأمر الذي سيتم تشغيله عند بدء الحاوية
# نفترض أن main.py هو نقطة الدخول الرئيسية للبوت

CMD gunicorn app:app &  python3 main.py
