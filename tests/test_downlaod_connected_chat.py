import os

import pytest

from tg_net_analysis.download_connected_chats import *



@pytest.mark.asyncio
async def test_make_record_dir():
    record_dir_path = await make_record_dir()
    assert os.path.isdir(record_dir_path)

@pytest.mark.asyncio
async def test_set_run_logs():
    record_dir_path = await make_record_dir()
    await set_run_logs(record_dir_path)
    assert os.path.exists(os.path.join(record_dir_path, "file.log"))

@pytest.mark.asyncio
async def test_create_csv_file():
    record_dir_path = await make_record_dir()
    filepath = os.path.join(record_dir_path, "test.csv")
    await create_csv_file(filepath, ["source", "test", "target"])
    assert os.path.exists(filepath)

@pytest.mark.asyncio
async def test_record_chats():
    record_dir_path = await make_record_dir()
    chats = [
        {
            "id": "test_username1",
            "label": "test_label1",
            "size": "test_size1",
            "seeding_chat": "test_seeding_chat1",
            "seed_connection_type": "type1"
        },
        {
            "id": "test_username2",
            "label": "test_label2",
            "size": "test_size2",
            "seeding_chat": "test_seeding_chat2",
            "seed_connection_type": "type2"

        }
    ]
    await record_chats(record_dir_path, chats)
