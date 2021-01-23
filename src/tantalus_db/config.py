from .base import Base
from sqlalchemy import Column, Boolean, Text


class Setting(Base):
    secret = Column(Boolean, nullable=False, default=False)
    name = Column(Text, nullable=False)
    value = Column(Text)


