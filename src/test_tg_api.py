import datetime

from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest

from api_config import config_register as cfg

# We have to manually call "start" if we want an explicit bot token
client = TelegramClient('test_client', api_id, api_hash)

async def main():
    # await client.send_message("me", "Hello world!")

    offset_date = datetime.date(2024, 12, 1)
    async for message in client.iter_messages("war_monitor", limit=15):
        if message.forward is not None:
            original_chat = message.forward.chat
            original_chat_id = message.forward.chat_id

            print("original chat:", original_chat)
            participants = await client.get_participants(original_chat.username, limit=0)
            participants = participants.total
            print("participants:", participants)
            print("original chat id:", original_chat_id)
            print("***")

            print("original_sender:", message.sender)
        # info = {
        #     "id": message.id,
        #     "text": message.text,
        #     "raw_text": message.raw_text,
        #     "forward": message.forward,
        #     "action_entities": message.action_entities
        # }
        # print(info)
            print("-"*90)

with client:
    client.loop.run_until_complete(main())