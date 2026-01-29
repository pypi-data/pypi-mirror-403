from uuid import uuid4
import os 
from dotenv import load_dotenv

from memsuite.store import MemoryStore

load_dotenv()

DB_URL = os.environ['DB_URL'] 

def test_write_and_read_memory():
    store = MemoryStore(DB_URL)

    user_id = uuid4()
    session_id = uuid4()

    store.write(
        user_id=user_id,
        session_id=session_id,
        agent_id="chatbot",
        content="hello",
        memory_type="conversation",
    )

    store.write(
        user_id=user_id,
        session_id=session_id,
        agent_id="chatbot",
        content="hi there",
        memory_type="conversation",
    )

    memories = store.read(
        user_id=user_id,
        session_id=session_id,
        memory_type="conversation",
    )

    assert len(memories) == 2
    assert memories[0].content == "hello"
    assert memories[1].content == "hi there"

test_write_and_read_memory()