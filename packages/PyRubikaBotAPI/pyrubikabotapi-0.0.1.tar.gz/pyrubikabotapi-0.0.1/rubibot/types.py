import json


class Update:
    def __init__(self, update):
        self._update = json.loads(update)
        if self._update.get("update"):
            self.dict = self._update.get("update")
        else:
            self.dict = self._update
        

class AuxData:
    def __init__(self, start_id, button_id):
        self.start_id = start_id
        self.button_id = button_id


class File:
    
    def __init__(self, file_id, file_name, size):
        self.id = file_id
        self.name = file_name
        self.size = size

class Chat:
    def __init__(self, chat_id, chat_type, user_id, first_name, last_name, title, username):
        self.id = chat_id
        self.type = chat_type
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.title = title
        self.username = username


class ForwardedFrom:
    def __init__(self, type_, message_id, chat_id, sender_id):
        self.type = type_
        self.message_id = message_id
        self.chat_id = chat_id
        self.sender_id = sender_id



class Location:
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


class Sticker:
    def __init__(self, sticker_id: str, file: File, emoji_character: str):
        self.id = sticker_id
        self.file = file
        self.emoji_character= emoji_character

class Contact:
    def __init__(self, first_name, last_name, phone_number):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number

class PollStatus:
    def __init__(self, state, selection_index, percent_vote_options, total_vote, show_total_votes):
        self.state = state
        self.selection_index = selection_index
        self.percent_vote_options = percent_vote_options
        self.total_vote = total_vote
        self.show_total_votes = show_total_votes

class Poll:
    def __init__(self, question, options, status: PollStatus):
        self.question = question
        self.options = options
        self.status = status


class Bot:

    def __init__(self, bot_id, bot_title, bot_avatar: File, description , username, start_message, share_url):
        self.id = bot_id
        self.title = bot_title
        self.avatar = bot_avatar
        self.description = description
        self.username = username
        self.start_message = start_message
        self.share_url = share_url

    
class BotCommand:
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description
    def _get_data(self):
        return {
            "command": self.command,
            "description": self.description
        }


class ChatPoll:
    def __init__(self, question):
        self.question = question
        self.options = []

    def add_options(self, *args: str):
        if len(self.options) < 10:
            if len(args) + len(self.options) > 10:
                raise ValueError("You cannot add more than 10 options!")
            for arg in args:
                self.options.append(arg)

    def _get_data(self):
        return {
            "question": self.question,
            "options": self.options
        }
    


class ChatKeypad:
    """
    
    
    """

    def __init__(self, resize_keyboard=False, on_time_keyboard=False):
        self.keypad_rows = {"rows": []} 
        self._data = {"resize_keyboard": resize_keyboard, "on_time_keyboard": on_time_keyboard}
        self.type = "New"

    def add(self, *keypad_rows):
        for kr in keypad_rows:
            self.keypad_rows["rows"].append(kr._get_data())

        self._data["rows"] = self.keypad_rows.get("rows")
    def _get_data(self):
        return self._data

    def _get_type(self):
        return self.type


class ChatKeypadRemove:
    def __init__(self):
        self.type = "Remove"

    def _get_type(self):
        return self.type


class InlineKeypad:

    def __init__(
            self,
            resize_keyboard = False,
            on_time_keyboard = False
        ): # ): (: /: |:

        
        self._data = {"rows": [], "resize_keyboard": resize_keyboard, "on_time_keyboard": on_time_keyboard}
        
    def add(self, *args):

        if not self._data.get("rows"):
            self._data["rows"] = []
        for kr in args:
            self._data["rows"].append(kr._get_data())

    def _get_data(self):
        return self._data

class KeypadRow:
    def __init__(self):
        self._data = {}


    def add(self, *buttons):
        self._data["buttons"] = []
        for btn in buttons:
            self._data["buttons"].append(btn._get_data())

    def _get_data(self):
        return self._data
    

class KeypadSimpleButton:
    def __init__(self, text, id):
        

        self.id = id
        self.text = text
        self.type = "Simple"
        self._data = {}

    def _set_data(self):
        self._data["id"] = self.id
        self._data["type"] = self.type
        self._data["button_text"] = self.text

        return self._data

    def _get_data(self):
        return self._set_data()


class Message:
    def __init__(
            self, type_: str, chat_id: str, message_id: str,
            text: str, time: float, is_edited: bool, sender_type: str, sender_id: str,
            aux: AuxData, reply_to_message_id: str, forwarded_from: ForwardedFrom,
            file: File, location: Location, sticker: Sticker, contact: Contact, poll: Poll
        ):

        self.type = type_
        self.chat_id = chat_id
        self.message_id = message_id
        self.text = text
        self.time = time
        self.is_edited = is_edited
        self.sender_type = sender_type
        self.sender_id = sender_id
        self.aux = aux
        self.reply_to_message_id = reply_to_message_id
        self.forwarded_from = forwarded_from
        self.file = file
        self.location = location
        self.sticker = sticker
        self.contact = contact
        self.poll = poll
        
    def _get_content_type(self):
        if self.file and self.file.id: return "file"
        if self.location and self.location.latitude is not None: return "location"
        if self.sticker and self.sticker.id: return "sticker"
        if self.contact and self.contact.phone_number: return "contact"
        if self.poll and self.poll.question: return "poll"
        return "text"

    def __repr__(self):
        return f"<rubibot.types.Message chat={self.chat_id} text={self.text}>"