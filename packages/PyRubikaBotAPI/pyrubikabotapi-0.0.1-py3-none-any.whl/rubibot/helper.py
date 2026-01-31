import requests
from rubibot.types import AuxData, Contact, File, ForwardedFrom, Location, Message, Poll, PollStatus, Sticker
def _to_message(raw) -> Message:

    type_ = raw.get("type")
    chat_id = raw.get("chat_id")
    # removed_message_id = raw.get("removed_message_id") # In the new update. soon...
    new_message = raw.get("new_message")
    # updated_message = raw.get("updated_message") # In the new update. soon...
    message_id = new_message.get("message_id")
    text = new_message.get("text")
    time = new_message.get("time")
    is_edited : bool = new_message.get("is_edited")
    sender_type = new_message.get("sender_type") # User or Bot
    sender_id = new_message.get("sender_id")
    aux_data = new_message.get("aux_data", {})
    aux = AuxData(aux_data.get("start_id"), aux_data.get("button_id"))
    reply_to_message_id = new_message.get("reply_to_message_id")
    forwarded_from_data = new_message.get("forwarded_from", {})
    type_forward = forwarded_from_data.get("type_from")
    forward_message_id = forwarded_from_data.get("message_id")
    forward_chat_id = forwarded_from_data.get("from_chat_id")
    forward_sender_id = forwarded_from_data.get("from_sender_id")
    forwarded_from = ForwardedFrom(type_forward, forward_message_id, forward_chat_id, forward_sender_id)
    file_data = new_message.get("file", {})
    file_id = file_data.get("file_id")
    file_name = file_data.get("file_name")
    file_size = file_data.get("size")
    file = File(file_id, file_name, file_size)
    location_data = new_message.get("location", {})
    longitude = location_data.get("longitude")
    latitude = location_data.get("latitude")
    location = Location(longitude, latitude)
    sticker_data = new_message.get("sticker", {})
    sticker_id = sticker_data.get("sticker_id")
    sticker_file_data = sticker_data.get("file", {})
    sticker_file_id = sticker_file_data.get("file_id")
    sticker_file_name = sticker_file_data.get("file_name")
    sticker_file_size = sticker_file_data.get("size")
    sticker_file = File(sticker_file_id, sticker_file_name, sticker_file_size)
    sticker_emoji_character = sticker_data.get("emoji_character")
    sticker = Sticker(sticker_id, sticker_file, sticker_emoji_character)
    contact_data = new_message.get("contact_message", {})
    contact_phone_number = contact_data.get("phone_number")
    contact_first_name = contact_data.get("first_name")
    contact_last_name = contact_data.get("last_name")
    contact = Contact(contact_first_name, contact_last_name, contact_phone_number)
    poll_data = new_message.get("poll", {})
    poll_question = poll_data.get("question")
    poll_options = poll_data.get("options")
    poll_status_data = poll_data.get("poll_status", {})
    poll_status_state = poll_status_data.get("state")
    poll_status_selection_index = poll_status_data.get("selection_index")
    poll_status_percent_vote_options = poll_status_data.get("percent_vote_options")
    poll_status_total_vote = poll_status_data.get("total_vote")
    poll_status_show_total_votes: bool = poll_status_data.get("show_total_votes")
    poll_status = PollStatus(
        poll_status_state,
        poll_status_selection_index,
        poll_status_percent_vote_options,
        poll_status_total_vote,
        poll_status_show_total_votes
    )
    poll = Poll(poll_question, poll_options, poll_status)



    message = Message(
        type_,
        chat_id,
        message_id,
        text,
        time,
        is_edited,
        sender_type,
        sender_id,
        aux,
        reply_to_message_id,
        forwarded_from,
        file,
        location,
        sticker,
        contact,
        poll
    )

    return message


def _chek_result_request(res):
        res = res.json()
        if res["status"] != "OK":
            error = res.get('dev_message', res.get('status'))
            raise Exception("Rubika Error: {}".format(error))
        data = res.get("data", {})
        if data.get('message_id'):
            return data.get('message_id')
        if data.get('file_id'):
            return data.get('file_id')
        if data.get('upload_url'):
             return data.get('upload_url')
        if data.get('download_url'):
            return data.get('download_url')
        return None


def _make_request(token, method_name, data=None):
    result = requests.post("https://botapi.rubika.ir/v3/{0}/{1}".format(token, method_name), json=data)
    return _chek_result_request(result)