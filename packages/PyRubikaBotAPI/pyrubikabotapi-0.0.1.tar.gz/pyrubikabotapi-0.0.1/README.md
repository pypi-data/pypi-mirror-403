# PyRubikaBotAPI

یک کتابخانه برای ساخت ربات‌های روبیکا با پایتون

## نصب
```bash
pip install PyRubikaBotAPI

```

## مثال ساده

```python
from rubibot import RubiBot

bot = RubiBot("YOUR_TOKEN")

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat_id, "سلام! خوش آمدید!")

bot.polling()
```

## مثال پیشرفته تر
```py
@bot.message_handler(content_types=['file'])
def handle(msg):
    file_id = msg.file.id
    file_url = bot.get_file(file_id)
    file = bot.download_file(file_url)
    with open('file.format', 'wb') as f
        f.write(file)
    # استفاده از فایل ارسالی
```

## مستندات:

Rubika: https://rubika.ir/pyrubikabotapi
GitHub: https://github.com/alireza-sadeghian/PyRubikaBotAPI