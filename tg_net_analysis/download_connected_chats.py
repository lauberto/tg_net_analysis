import os
import re
import csv
import logging
import random
import time
from argparse import ArgumentParser
from datetime import datetime
from typing import List, Mapping, Union

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl import types
from telethon.errors.rpcerrorlist import UsernameInvalidError, ChannelPrivateError

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

load_dotenv()

api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
client = TelegramClient('test_client', api_id, api_hash)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
    handlers=[stream_handler]
)

logger = logging.getLogger(__name__)

async def find_tg_channel_link(text: str):
    if text is not None and text != "None":
        tg_links = re.findall(r"https:\/\/t\.me\/(\w+)", text)
        return tg_links
    return None

async def _get_participants_number(client, chat_username: str):
    if chat_username is not None and chat_username != "None":
        participants = await client.get_participants(chat_username, limit=0)
        participants = participants.total
        return participants
    return None

async def _clean_chat_id(id_: int):
    str_id = str(id_)
    if str_id.startswith("-100"):
        str_id = str_id[4:]
    return int(str_id)

async def get_chat_info(client, seed, message):
    """
    Check if message was forward and, in that case,
    collect info about the source chat.
    """

    # Forwards
    if message.forward is not None and message.forward.chat is not None:
        print(message.id, message.date, message.text)
        # collect and record username, title and size
        original_chat = message.forward.chat
        if type(original_chat) not in (types.Chat, types.Channel):
            return None
        # original_chat_username = original_chat.username
        original_chat_id = original_chat.id
        original_chat_title = original_chat.title

        # FIXME: this should not stay as a try/except block
        try: 
            participants = await _get_participants_number(client, original_chat_id)
        except ChannelPrivateError:
            logger.debug("FORWARD: Tried to get messages from %s but chat is private: Setting participants to None.", original_chat_title)
            participants = None
    
        original_chat_id = await _clean_chat_id(original_chat_id)
        seed = await _clean_chat_id(seed)
        chat_info = {
            "id": original_chat_id,
            "label": original_chat_title,
            "size": participants,
            "seeding_chat": seed,
            "connection_type": "forward",
            "connection_date": message.date
        }
        return chat_info
    
    # Mentions
    tg_links = await find_tg_channel_link(message.message)
    if tg_links is not None:
        for match in tg_links:
            original_chat_username = match

            try:
                entity = await client.get_entity(original_chat_username)
            except (UsernameInvalidError, ValueError):
                return None

            if type(entity) not in (types.Chat, types.Channel):
                return None 
            original_chat_id = entity.id
            original_chat_title = entity.title

            # FIXME: this should not stay as a try/except block
            try: 
                participants = await _get_participants_number(client, original_chat_id)
            except ChannelPrivateError:
                logger.debug("MENTION: Tried to get messages from %s but chat is private: Setting participants to None.", original_chat_title)
                participants = None

            original_chat_id = await _clean_chat_id(original_chat_id)
            seed = await _clean_chat_id(seed)
            chat_info = {
                "id": original_chat_id,
                "label": original_chat_title,
                "size": participants,
                "seeding_chat": seed,
                "connection_type": "mention",
                "connection_date": message.date
            }
            return chat_info
    
    return None


async def collect_forwards_original_chats(
        client,
        seed: str,
        offset_date: datetime,
        limit: float,
        reverse: bool = False,
    ) -> List[Mapping[str, Union[int, str]]]:
    """ Collect the chat usernames of the groups
        from which the forward messaged were originally created.
    """
    logger.debug("Collecting chats from: %s", seed)
    original_chats = []

    if offset_date is not None:
        reverse = True
        limit = None

    # FIXME: this try/except is made to temporarily work around the ChannelPrivateError
    try:
        async for message in client.iter_messages(seed, offset_date=offset_date, limit=limit, reverse=reverse, wait_time=2):
            time.sleep(2*random.random())
            chat_info = await get_chat_info(client, seed, message)
            original_chats.append(chat_info)
    except ChannelPrivateError:
        logger.debug("Could not collect messages from %s because channel is private and you probably don't have access.", seed)
        return []

    original_chats = [chat for chat in original_chats if chat is not None and chat["size"] is not None]    

    return original_chats

async def make_record_dir():
    record_dir = os.path.join(DATA_DIR, "run_" + datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    if not os.path.exists(record_dir):
        os.makedirs(record_dir)
    return record_dir

async def create_csv_file(
        filepath: str,
        columns: List[str]
    ):
    if not os.path.exists(filepath):
        with open(filepath, "w") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter="\t")
            csvwriter.writerow(columns)

async def record_chats(
        record_dir: str,
        original_chats: List[Mapping[str, Union[int, str]]]
    ):
    node_file = os.path.join(record_dir, "node.csv")
    await create_csv_file(node_file, ["id", "label", "size"])
    
    edge_file = os.path.join(record_dir, "edge.csv")
    await create_csv_file(edge_file, ["source", "target", "connection_type", "connection_date"])
    
    # record id, label, size of collected chats
    with open(node_file, "a") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        for chat in original_chats:
            csvwriter.writerow([chat["id"], chat["label"], chat["size"]])

    # record source, target, type to establish edges
    with open(edge_file, "a") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        for chat in original_chats:
            csvwriter.writerow([chat["seeding_chat"], chat["id"], chat["connection_type"], chat["connection_date"]])
    
async def set_run_logs(record_dir:str):
    logs_file = os.path.join(record_dir, "file.log")
    file_handler = logging.FileHandler(logs_file, mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-i",
        "--iterations",
        default=2,
        help="How many times should the scraping be iterated.",
        type=int
    )
    parser.add_argument(
        "-sf",
        "--seeds_file",
        default=os.path.join(FILE_DIR, "seeds.tsv"),
        help="Which TG channel usernames to use as seeds.",
        type=str
    )
    parser.add_argument(
        "-od",
        "--offset_date",
        # required=True,
        default=None,
        type=datetime.fromisoformat,
        help="Date is ISO format (year, month, day), e.g. 2022-02-14"
    )
    parser.add_argument(
        "-ml",
        "--message_limit",
        default=100,
        help="How many messages per chat should be collected starting from now and going backward in time?",
        type=int
    )
    args = parser.parse_args()
    return args

def _read_seeds_file(filepath):
    new_seeds = []
    # chat_title2id = {}
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            new_seeds.append(int((row["id"])))
    return new_seeds

# def _read_seeds_file(filepath):
#     with open(filepath, "r") as f:
#         seeds = [line.rstrip() for line in f]
#     return seeds

async def main():
    args = _parse_args()
    iterations = args.iterations
    new_seeds = _read_seeds_file(args.seeds_file)
    logger.debug("Seeds are: %s", ", ".join([str(seed) for seed in new_seeds]))
    record_dir = await make_record_dir()
    await set_run_logs(record_dir)

    while iterations > 0 and new_seeds:
        iterations -= 1
        original_chats = []

        for seed in new_seeds:
            collected_chats = await collect_forwards_original_chats(client, seed, args.offset_date, args.message_limit)
            original_chats.extend(collected_chats)

        # original_chats = list(set(original_chats))
        await record_chats(record_dir, original_chats)
        new_seeds = [chat["id"] for chat in original_chats]

    logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.StreamHandler)]

async def test():
    async for message in client.iter_messages(-1001318845663, limit=5, wait_time=1):
        print(message)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
        # client.loop.run_until_complete(test())
