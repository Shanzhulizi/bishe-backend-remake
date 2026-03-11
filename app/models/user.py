from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, text, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    profile = Column(JSONB, nullable=True)

    last_active_at = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    avatar = Column(Text, nullable=True)
