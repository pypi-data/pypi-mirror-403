import json
import os
import time
import requests
from typing import Any, List, Optional
from rubibot import helper
from rubibot import types

# In the name of Allah
# Developer: Alireza Sadeghian
# URL: https://github.com/alireza-sadeghian/PyRubikaBotAPI
# Channel: https://rubika.ir/pyrubikabotapi
# Faghat Heydar Amiralmomenin ast

"""
Welcome to PyRubikaBotAPI

"""

class RubiBot:
    """
    This is a main class for RubiBot
    Using this class, you can define handlers for your Rubika robots and respond appropriately to updates using methods.

    for example:
        
        import rubibot
        bot = rubibot.RubiBot('TOKEN') # You need to get this token from @BotFather
        # Now you can define handlers for your bot and use methods.
    
    See more examples on our Rubika channel.
    https://rubika.ir/PyRubikaBotAPI

    توضیحات فارسی: 
    این اصلی ترین کلاس برای ربات شماست
    برای استفاده از امکانات کتابخانه یک شیء از این کلاس ایجاد کنید
    

    """

    def __init__(self, token):
        self.TOKEN = token
        self.BASE_URL = f"https://botapi.rubika.ir/v3/{self.TOKEN}"
        self._message_handlers = []
        self.OFFSET_FILE = "noi.json" # noi: n → next, o → offset, i → id

    def message_handler(
            self,
            commands: Optional[List[str]]=None,
            content_types: Optional[List[str]]=None
    ):
        """
        It is responsible for managing messages received from the user. 
        It handles all types of messages such as text, video, Voice, Poll, etc.
        As a parameter to the decorator function, it passes :class:`rubibot.types.Message` object.
        All message handlers are stored and executed in the order in which they are written.

        for example:
            
            bot = RubiBot('token')

            # Handle /start command
            @bot.message_handler(commands=['start'])
            def start(message: rubibot.types.Message):
                bot.send_message(message.chat_id, "Hello from RubiBot!")

            # Handle all sticker messages
            @bot.message_handler(content_types=['sticker'])
            def sticker_handler(message):
                bot.send_file(message.chat.id, message.sticker.file.id, "This is your sticker image")
            
            # Handle all sent messages of text type
            @bot.message_handler()
            def handler(message):
                bot.reply_to(chat_id=message, text=message.text)
        
        :param commands: list of commands

        :param content_types: Supported message content types ↓
        ['text', 'file', 'location', 'sticker', 'contact', 'poll']

        :return: decorated function

        توضیحات فارسی:
        این تابع پیام های دریافتی و بروزرسانی هارا مدیریت می کند
        برای استفاده از این تابع یک دکوریتور از آن ایجاد کنید و تابع مورد نظر
        برای هندل کردن پیام هارا به عنوان تابع ورودی برای دکوریتور تعریف کنید

        این دکوریتور یک شیء از کلاس مسیج
        از پیام دریافتی توسط کاربر را به عنوان ورودی به تابعی که مشخص کرده اید می دهد

        هندلر های پیام به ترتیب افزوده شدن اجرا می شوند
        و بیش از یک هندلر برای یک پیام اجرا نمی شود!

        پارامتر ها:
        commands: لیست دستوراتی که میخواهید هندلر شما فقط آنها را هندل کند
        content_types: فیلتر کردن نوع محتوا برای هندل شدن در هندلر شما

        جهت دیدن مثال های بیشتر و دریافت سورس کد های
        آماده و آزمایشی به کانال ما در سوپراپلیکیشن روبیکا سر بزنید
        https://rubika.ir/PyRubikaBotAPI
        """


        LISTOFCONTENTTYPES = ['text', 'file', 'location', 'sticker', 'contact', 'poll']
        
        if isinstance(commands, str):
            commands = [commands]
        
        if content_types is None:
            content_types = ['text']
        
        if isinstance(content_types, str):
            content_types = [content_types]

        for ct in content_types:
            if ct not in LISTOFCONTENTTYPES:
                raise ValueError(f"{ct} is not supported, supported values: {LISTOFCONTENTTYPES}")

        def decorator(handler):
            self._message_handlers.append({
                    "handler": handler,
                    "filters": {
                        "commands": commands,
                        "content_types": content_types
                    }
                })
            return handler
            
        
        return decorator


    def get_updates(self,offset=None, limit=10):
        """
        for get updates from rubika

        :param offset: If you want to receive only new updates when receiving updates, put the value `next_offset_id` from the previous request here. If you leave nothing, by default all previous updates will be sent in this request.

        :param limit: Limit on number of updates, Default: 10

        :return: Tuple of(updates, next_ofsset_id) # for polling

        """
        if limit > 100 or limit < 1:
            raise ValueError("The limit cannot be greater than 100 and less than 1.")
        
        params = {"limit": limit}
        if offset:
            params["offset_id"] = offset
        try:
            res = requests.post(f"{self.BASE_URL}/getUpdates", json=params, timeout=15)
        except Exception as e:
            raise Exception("Error: {}".format(e))
        data = res.json()
        if not res or res.status_code !=200:
            raise Exception("Error in receiving updates: {}".format(data.get("status")))
        
        updates = []
        for upd in data.get("data", {}).get("updates"):
            updates.append(types.Update(json.dumps(upd)))
        return updates, data.get("data").get("next_offset_id")
    
    
    def __load_offset(self):
        if not os.path.exists(self.OFFSET_FILE):
            self.__save_offset(None)
            return None
    
        with open(self.OFFSET_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("next_offset_id")

    def __save_offset(self, offset_id):
        with open(self.OFFSET_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"next_offset_id": offset_id},
                f,
                ensure_ascii=False,
                indent=4
            )
    
    def polling(self, t: int = 2, limit=10):
        """
        This function receives updates from Rubica indefinitely and repeatedly at specified intervals and manages them using written handlers.

        **Warning: This method is only for testing the bot in local mode and should not be used as the main method for receiving and handling updates. This method is not optimal and if you do this, a large number of requests will be sent to Rubika and you will be limited.

        :param t: The time interval between requests

        :param limit: Limit the number of updates received per request

        :return: 

        توضیحات فارسی:
        در ابتدا دقت کنید که از این تابع فقط و فقط به صورت آزمایشی و برای 
        تست کردن ربات خود استفاده کنید و به هیچ عنوان برای دریافت آپدیت ها
        به صورت دائم از این متود استفاده نکنید و به جای آن 
        از وبهوک استفاده کنید

        این متد را در آخر سورس کد خود فراخوانی کنید تا بروزرسانی ها را در بازه
        های زمانی مشخص از روبیکا دریافت کند و توسط هندلر های ایجاد شده توسط شما هندل کند
        """
        next_offset_id = self.__load_offset()

        while True:
            updates, next_offset_id = self.get_updates(offset=next_offset_id, limit=limit)
            if not next_offset_id:
                next_offset_id = self.__load_offset()
            self.__save_offset(next_offset_id)
            self.process_new_updates(updates)
            time.sleep(t)

    def send_message(
            self,chat_id,text,
            chat_keypad=None,
            inline_keypad=None,
            disable_notification=False,
            _reply_to_message_id = None
        ):

        """
        Use this method to send text messages.

        **Warning: Do not send more than about 4096 characters each message

        :param chat_id: The unique identifier of a chat, such as a private conversation or a group/Channel
        :type chat_id: :obj:`str`

        :param text: Text to send
        :type text: :obj:`str`

        :param chat_keypad: Buttons at the bottom of the page that are sent with the message
        :type chat_keypad: :obj:`rubibot.types.ChatKeypad` or :obj:`rubibot.types.ChatKeypadRemove`

        :param inline_keypad: In-text buttons that appear below the message text
        :type inline_keypad: :obj:`rubibot.types.InlineKeypad`

        :param disable_notification: Send a message with silent notification
        :type disable_notification: :obj:`bool`

        :param _reply_to_message_id: It is used to reply to messages,
        but you should use :method:`rubibot.RubiBot.reply_to()` to reply to plain text.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`

        توضیحات فارسی:
        از این متود برای ارسال پیام متنی به یک چت مشخص استفاده کنید
        طول پیام شما نباید بیشتر از 4096 کاراکتر باشد و گرنه خطا دریافت می کنید
        
        پارامتر ها:

        chat_id: شناسه چت مورد نظر برای ارسال پیام متنی
        text: پیام مورد نظر
        chat_keypad: اگر میخواهید همراه با پیام، دکمه هایی در پایین صفحه برای کاربر ارسال شود
        ابتدا کی پد خود را با استفاده از:
        `rubibot.types.ChatKeypad`
        ایجاد کنید و آن را در اینجا قرار دهید
        inline_keypad: اگر میخواهید دکمه هایی در زیر پیام ارسالی ایجاد شود ابتدا کی پد خود را با استفاده از:
        `rubibot.types.InlineKeypad` 
        ایجاد کنید و سپس آن را اینجا قرار دهید
        disable_notification: اگر میخواهید پیام شما با اعلان بدون صدا ارسال شود این مقدار را برابر 
        `True` قرار دهید
        """

        data = {"chat_id": chat_id, "text": text}

        if chat_keypad:
            type_ = chat_keypad.type
            data["chat_keypad_type"] = type_
            if type_ != "Remove":
                data["chat_keypad"] = chat_keypad._get_data()

        if inline_keypad:
            data["inline_keypad"] = inline_keypad._get_data()

        if disable_notification:
            data["disable_notification"] = True

        if _reply_to_message_id:
            data["reply_to_message_id"] = _reply_to_message_id
 
        method_name = 'sendMessage'
        return helper._make_request(self.TOKEN, method_name, data)
        
    

    def reply_to(
            self, message: types.Message,
            text, chat_keypad=None,
            inline_keypad=None,
            disable_notification=False
        ):
        """
        Send a text message as a reply
        This function is for your convenience in sending text messages as replies, but to send other types of messages as replies, you must use the `reply_to_message_id` value available in those methods.

        :param message: message to reply
        :type message: :obj:`rubibot.types.Message`

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`

        توضیحات فارسی:
        برای ارسال پیام های متنی و ریپلای کردن آن ها از این متود استفاده کنید
        """
        

        return self.send_message(
                message.chat_id, text,
                chat_keypad, inline_keypad,
                disable_notification, 
                message.message_id
                )
        

    def get_me(self):
        """
        It does not receive any input and returns information about the bot.

        :return: Bot information
        :rtype: :obj:`rubibot.types.Bot`
        """
        res = requests.post("{}/getMe".format(self.BASE_URL))
        r = res.json().get("data")
        bot = r.get("bot")
        bot_id = bot.get("bot_id")
        bot_title = bot.get("bot_title")
        avatar = bot.get("avatar", {})
        avatar_id = avatar.get("file_id")
        avatar_name = avatar.get("file_name")
        avatar_size = avatar.get("size")
        avatar_ = types.File(avatar_id, avatar_name, avatar_size)
        description = bot.get("description")
        username = bot.get("user_name")
        start_msg = bot.get("start_message")
        share_url = bot.get("share_url")

        return types.Bot(bot_id, bot_title, avatar_, description, username, start_msg, share_url)
    
    def send_poll(self, chat_id: str, poll: types.ChatPoll):
        """
        Send a poll to a specific chat

        :param chat_id: Desired chat ID
        :type chat_id: :obj:`str`

        :param poll: Desired poll
        :type poll: :obj:`rubibot.types.ChatPoll`

        :return: On success, the send message id is returned
        :rtype: :obj:`str`
        """
        data = poll._get_data()
        data["chat_id"] = chat_id
        method_name = 'sendPoll'
        return helper._make_request(self.TOKEN, method_name, data)
        
    
    def send_contact(
            self, chat_id: str, first_name: str, last_name: str,
            phone_number: str, chat_keypad: types.ChatKeypad= None,
            inline_keypad: types.InlineKeypad = None, disable_notification: bool = False,
            reply_to_message_id: str = None
    ):
        """
        Send a contact to a specific chat

        :param chat_id: Desired Chat ID
        :type chat_id: :obj:`str`

        :param first_name: Contact's first name
        :type first_name: :obj:`str`

        :param last_name: Contact's last name
        :type last_name: :obj:`str`

        :param phone_number: Contact's phone number
        :type phone_number: :obj:`str`
        
        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`

        """
        data = {
            "chat_id": chat_id,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number
        }

        if chat_keypad:
            type_ = chat_keypad.type
            data["chat_keypad_type"] = type_
            data["chat_keypad"] = chat_keypad._get_data()

        if inline_keypad:
            data["inline_keypad"] = inline_keypad._get_data()

        if disable_notification:
            data["disable_notification"] = True

        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
 
        method_name = 'sendContact'
        return helper._make_request(self.TOKEN, method_name, data)

    def get_chat(self, chat_id: str):
        """
        Get the desired chat information, including name and username.

        :param chat_id: Desired Chat ID
        :type chat_id: :obj:`str`

        :return: Chat information
        :rtype: :obj:`rubibot.types.Chat`

        """
        data = {
            "chat_id": chat_id
        }

        res = requests.post("{}/getChat".format(self.BASE_URL), json=data)
        data = res.json().get("data")
        if data:
            chat = data.get("chat")
            chat_id = chat.get("chat_id")
            chat_type = chat.get("chat_type")
            user_id = chat.get("user_id")
            first_name = chat.get("first_name")
            last_name = chat.get("last_name")
            title = chat.get("title")
            username = chat.get("username")    
            return types.Chat(chat_id, chat_type, user_id, first_name, last_name, title, username)
        else:
            raise Exception("Rubika Error: {}".format(res.json().get("status")))
        


    def forward(self, from_chat_id: str, to_chat_id: str, message_id: str, disable_notification: bool = False):
        """
        forward a message

        """
        data = {
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "to_chat_id": to_chat_id,
            "disable_notification": disable_notification
        }

        method_name = 'forwardMessage'
        return helper._make_request(self.TOKEN, method_name, data)

    def edit_message(
            self, chat_id: str, message_id: str,
            new_text: str, new_inline_keypad: types.InlineKeypad = None
        ):
        """
        Edit a message

        توضیحات فارسی:
        
        پارامتر های قابل توضیح:
        new_text: متنی که میخواهید جایگزین متن قبلی شود
        new_inline_keypad: اگر میخواهید دکمه های درون متنی خود را نیز تغییر بدهید، مقدار جدیدی برای این ورودی قرار دهید
        """
        
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text
        }

        method_name = 'editMessageText'
        helper._make_request(self.TOKEN, method_name, data)

        if new_inline_keypad:
            data.pop("text")
            data["inline_keypad"] = new_inline_keypad._get_data()

            method_name = 'editMessageKeypad'
            return helper._make_request(self.TOKEN, method_name, data)
        
        return True

    def delete_message(self, chat_id: str, message_id: str):
        """
        Delete a message

        """
        data = {
            "chat_id": chat_id,
            "message_id": message_id
        }

        method_name = 'deleteMessage'
        return helper._make_request(self.TOKEN, method_name, data)
    
    def set_commands(self, *args):
        """
        Setting commands for the bot, this way any new user who logs into your bot will see the commands you register here in the user interface and can use them.

        :param args: Desired commands
        :type args: :obj:`rubibot.types.BotCommand`

        :return: On success, return True
        :rtype: :obj:`bool`

        """
        data = {
            "bot_commands": []
        }
        for arg in args:
            data["bot_commands"].append(arg._get_data())

        method_name = 'setCommands'
        return helper._make_request(self.TOKEN, method_name, data)


    def edit_chat_keypad(self, chat_id: str, chat_keypad):
        """
        Edit ChatKeypad

        """
        data = {"chat_id": chat_id}
        type_ = chat_keypad._get_type()
        data["chat_keypad_type"] = type_
        if type_ != "Remove":
            data["chat_keypad"] = chat_keypad._get_data()

        method_name = 'editChatKeypad'
        return helper._make_request(self.TOKEN, method_name, data)
    
    def set_webhook(self, url, type="ReceiveUpdate"):
        data = {"url": url, "type": type}
        method_name = 'updateBotEndpoints'
        return helper._make_request(self.TOKEN, method_name, data)
        
    
    def get_file(self, file_id):
        """
        Get the download address of a file by file ID

        for example:
            
            download_url = bot.get_file('file_id')
            file = bot.download_file(download_url)
            # Now the file sent from the user has been downloaded and stored in the file variable.
        
        :param file_id: The file id
        :type file_id: :obj:`str`

        :return: file download url
        :rtype: :obj:`str`

        توضیحات فارسی:
        آیدی فایل را به عنوان ورودی قرار دهید تا لینک دانلود به شما بازگردانده شود
        با لینک دانلود میتوانید فایل را دانلود کنید

        """
        data ={
            "file_id": file_id
        }

        method_name = 'getFile'
        return helper._make_request(self.TOKEN, method_name, data)

    def download_file(self, file_url) -> bytes:
        """
        Download a file by download URL

        :param file_url: The file url
        :type file_url: :obj:`str`

        :return: The File
        :rtype: :obj:`bytes`

        توضیحات فارسی:
        لینک دانلود را به عنوان ورودی قرار دهید تا فایل مورد نظر به عنوان
        خروجی به شما تحویل داده شود

        """
        res = requests.get(file_url)
        if res.status_code != 200:
            raise Exception(f"Download File Error")
        return res.content

    def request_send_file(self, file_type):
        """
        Request to upload a file to Rubika servers

        توضیحات فارسی:
        درخواست برای آپلود یک فایل روی سرور های روبیکا
        * به صورت پیشفرض نیازی به استفاده از این متود ندارید 
        و برای ارسال فایل به یک چت می توانید از متود های زیر استفاده کنید:
        `rubibot.RubiBot.send_photo`
        `rubibot.RubiBot.send_file`
        و دیگر متود های ارسال فایل
    
        """
        if file_type not in ['File', 'Image', 'Voice', 'Video', 'Music', 'Gif']:
            raise ValueError("Sorry")
        data = {"type": file_type}
        method_name = 'requestSendFile'
        return helper._make_request(self.TOKEN, method_name, data)
        
    
    def __send_file(
            self, file_type, chat_id, file, text, chat_keypad: types.ChatKeypad, inline_keypad: types.InlineKeypad, reply_to_message_id, disable_notification
        ):

        data = {"chat_id": chat_id, "text": text}

        if chat_keypad:
            data["chat_keypad_type"] = chat_keypad._get_type()
            data["chat_keypad"] = chat_keypad._get_data()
        if inline_keypad:
            data["inline_keypad"] = inline_keypad._get_data()
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if disable_notification:
            data["disable_notification"] = disable_notification

        upload_url = self.request_send_file(file_type)
        
        data["file_id"] = self.upload_file(file, upload_url)
    
        method_name = 'sendFile'
        return helper._make_request(self.TOKEN, method_name, data)
    
    def _create_file_type(self, file):
        if hasattr(file, "read"):
            return file
        elif isinstance(file, str):
            return open(file, 'rb')
        else:
            raise ValueError('invalid type')

    def upload_file(self, file, upload_url):
        file = self._create_file_type(file)
        files = {"file": ("file", file)}
        res = requests.post(
            upload_url,
            files=files
        )
        file.close()
        
        return helper._chek_result_request(res)
        
    def send_photo(
            self, chat_id: str, photo: Any,
            text: str, chat_keypad: Optional[types.ChatKeypad]=None,
            inline_keypad: Optional[types.InlineKeypad]=None, 
            reply_to_message_id:Optional[str]=None, disable_notification: bool=False
        ):
        """
        Send an image with a maximum size of 10 MB.
        Supported formats: PNG, JPG, GIF, WEBP

        :param photo: the photo to send
        :type photo: :obj:`bytes` or File Path in Disk

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`
        """

        return self.__send_file(
            "Image", chat_id, photo, text, chat_keypad, inline_keypad,
            reply_to_message_id, disable_notification
        )
        
    def send_voice(
            self, chat_id: str, voice: Any,
            text: str, chat_keypad: Optional[types.ChatKeypad]=None,
            inline_keypad: Optional[types.InlineKeypad]=None, 
            reply_to_message_id:Optional[str]=None, disable_notification: bool=False
        ):
        """
        Send a Voice.
        Supported formats: MP3

        :param voice: the voice to send
        :type voice: :obj:`bytes` or File Path in Disk

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`
        """

        return self.__send_file(
            "Voice", chat_id, voice, text, chat_keypad, inline_keypad,
            reply_to_message_id, disable_notification
        )
    
    def send_video(
            self, chat_id: str, video: Any,
            text: str, chat_keypad: Optional[types.ChatKeypad]=None,
            inline_keypad: Optional[types.InlineKeypad]=None, 
            reply_to_message_id:Optional[str]=None, disable_notification: bool=False
        ):
        """
        Send a Video with a maximum size of 50 MB.
        Supported formats: MP4

        :param video: the video to send
        :type video: :obj:`bytes` or File Path in Disk

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`
        """

        return self.__send_file(
            "Video", chat_id, video, text, chat_keypad, inline_keypad,
            reply_to_message_id, disable_notification
        )
    
    def send_gif(
            self, chat_id: str, gif: Any,
            text: str, chat_keypad: Optional[types.ChatKeypad]=None,
            inline_keypad: Optional[types.InlineKeypad]=None, 
            reply_to_message_id:Optional[str]=None, disable_notification: bool=False
        ):
        """
        Send a Gif that must be without sound.
        Supported formats: MP4

        :param gif: the gif to send
        :type gif: :obj:`bytes` or File Path in Disk

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`
        """

        return self.__send_file(
            "Gif", chat_id, gif, text, chat_keypad, inline_keypad,
            reply_to_message_id, disable_notification
        )
    
    def send_file(
            self, chat_id: str, file: Any,
            text: str, chat_keypad: Optional[types.ChatKeypad]=None,
            inline_keypad: Optional[types.InlineKeypad]=None, 
            reply_to_message_id:Optional[str]=None, disable_notification: bool=False
        ):
        """
        Send an other files with a maximum size of 50MB.
        Supported formats: all

        :param file: the file to send
        :type file: :obj:`bytes` or File Path in Disk

        The rest of the values ​​are the same as those defined in `rubibot.RubiBot.send_message()`.

        :return: On success, the send message id is returned
        :rtype: :obj:`str`

        """

        return self.__send_file(
            "File", chat_id, file, text, chat_keypad, inline_keypad,
            reply_to_message_id, disable_notification
        )

        
    def _test_message_handler(self, handler, message):
        filters = handler["filters"]
        if filters["commands"]:
            if not message.text:
                return False
            cmd = message.text.split()[0][1:]
            if cmd not in filters["commands"]:
                return False
            
        if filters["content_types"]:
            if message._get_content_type() not in filters["content_types"]:
                return False
        
        return True

    
    def process_new_updates(self, updates: list[types.Update]):
        """
        Processing new updates
        Usage instructions:
        First convert the received updates into an object of the `rubibot.types.Update` class and pass this object as input to this function

        Warning: The input to this function must be in the form of a list.

        for exapmle:
            
            update = rubibot.types.Update(myupdate) # Updates received from Webhook
            bot.process_new_updates([update])
            # Now the received update is processed by the handlers you defined. This is one of the most important steps in running your bot.

        see more example: 
        https://github.com/alireza-sadeghian/PyRubikaBotAPI

        :param updates: Received updates
        :type updates:  :obj:`list` of :obj:`rubibot.types.Updates`

        توضیحات فارسی:
        اگر از پولینگ استفاده می کنید نیازی به این ندارید
        اگر از وبهوک استفاده میکنید، ابتدا جیسون دریافتی را به شیء آپدیت 
        از کتابخانه روبی بات تبدیل کنید و سپس آن را به صورت لیست به عنوان ورودی این تابع قرار دهید
        تا با استفاده از هندلر هایی که ثبت کرده اید هندل شود
        """
        if not isinstance(updates, List):
            raise Exception("Invalid type for updates")

        for upd in updates:

            if not isinstance(upd, types.Update):
                raise Exception("Invalid type for update")
            
            message = helper._to_message(upd.dict)
            for handler in self._message_handlers:
                if self._test_message_handler(handler, message):
                    handler["handler"](message)
                    break



# soon...               
# This is not the end of our work... 😎