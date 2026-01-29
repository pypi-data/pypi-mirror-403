from uuid import UUID
from typing import Dict, Any
from memsuite.db import SQLMemoryDB
from memsuite.models import Memory
from memsuite.config import validate_db_url


class MemoryStore : 

    def __init__(self, database_url: str) : 
        if not validate_db_url(database_url):
            raise ValueError(
                "Invalid database URL. Must start with 'postgresql://' or 'postgres://'"
            )
        self._db = SQLMemoryDB(database_url) 


    def write(self, 
              user_id: UUID,
              session_id : UUID, 
              agent_id: str, 
              content: str, 
              memory_type: str, 
              metadata: Dict[str, Any] | None = None, 
     ) -> None : 
        
        memory = Memory(
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            meta=metadata or {},
        )
        self._db.write(memory)

    def read(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """
        Retrieve memories scoped to a specific user and session.

        Both user_id and session_id are required to prevent unscoped global reads.
        """
        return self._db.read(
            user_id=user_id,
            session_id=session_id,
            memory_type=memory_type,
        )