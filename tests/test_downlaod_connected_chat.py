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



