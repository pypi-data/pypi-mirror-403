from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from uuid import UUID
from memsuite.models import Base, Memory


class SQLMemoryDB:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(
            database_url,
            future=True,
            echo=True,
            pool_size=3,
            max_overflow=0,
        )
        self._Session = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

        Base.metadata.create_all(self._engine)

    def write(self, memory: Memory) -> None:
        with self._Session() as session:
            session.add(memory)
            session.commit()

    def read(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        memory_type=None,
        agent_id=None,
    ) -> list[Memory]:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.session_id == session_id,
            )
            .order_by(Memory.created_at.asc())
        )

        if memory_type is not None:
            stmt = stmt.where(Memory.memory_type == memory_type)

        if agent_id is not None:
            stmt = stmt.where(Memory.agent_id == agent_id)

        with self._Session() as session:
            return list(session.scalars(stmt))

