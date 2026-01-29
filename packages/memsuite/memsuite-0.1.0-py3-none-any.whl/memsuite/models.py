import uuid 
from uuid import UUID
from typing import Dict, Any

from sqlalchemy import String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column 

class Base(DeclarativeBase) : 
    pass 

class Memory(Base) : 
    __tablename__ = "memories" 


    id : Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    agent_id: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)
    memory_type: Mapped[str] = mapped_column(String(32), index=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
