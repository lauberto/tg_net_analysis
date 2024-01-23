import os
import csv
import logging
import time
from datetime import datetime
from typing import List, Mapping, Union

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

load_dotenv()

with open(os.path.join(FILE_DIR, "seeds.txt"), "r") as f:
    seeds = [line.rstrip() for line in f]
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

async def collect_forwards_original_chats(client, seed: str) -> List[Mapping[str, Union[int, str]]]:
    """ Collect the chat usernames of the groups
        from which the forward messaged were originally created.
    """
    logger.debug("Collecting chats from: %s", seed)
    original_chats = []
    async for message in client.iter_messages(seed, limit=20):
        time.sleep(0.1)
        if message.forward is not None and message.forward.chat is not None:
            # collect and record username, title and size
            print(message.forward)
            original_chat = message.forward.chat
            print(original_chat)
            original_chat_username = original_chat.username
            original_chat_title = original_chat.title
            participants = await client.get_participants(original_chat_username, limit=0)
            participants = participants.total

            chat_info = {
                "id": original_chat_username,
                "label": original_chat_title,
                "size": participants,
                "seeding_chat": seed,
                "seed_connection_type": "forward"
            }

            original_chats.append(chat_info)

    return original_chats

async def make_record_dir():
    record_dir = os.path.join(DATA_DIR, "run_" + datetime.now().strftime("%d-%m-%Y_%H:%M:%S"))
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
    await create_csv_file(edge_file, ["source", "target", "seed_connection_type"])
    
    # record id, label, size of collected chats
    with open(node_file, "a") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        for chat in original_chats:
            csvwriter.writerow([chat["id"], chat["label"], chat["size"]])

    # record source, target, type to establish edges
    with open(edge_file, "a") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        for chat in original_chats:
            csvwriter.writerow([chat["seeding_chat"], chat["id"], chat["seed_connection_type"]])
    
async def set_run_logs(record_dir:str):
    logs_file = os.path.join(record_dir, "file.log")
    file_handler = logging.FileHandler(logs_file, mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

async def main():
    iterations = 2
    new_seeds = seeds
    record_dir = await make_record_dir()
    await set_run_logs(record_dir)

    while iterations > 0:
        iterations -= 1
        original_chats = []

        for seed in new_seeds:
            collected_chats = await collect_forwards_original_chats(client, seed)
            original_chats.extend(collected_chats)

        # original_chats = list(set(original_chats))
        await record_chats(record_dir, original_chats)
        new_seeds = [chat["id"] for chat in original_chats]

    logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.StreamHandler)]

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
