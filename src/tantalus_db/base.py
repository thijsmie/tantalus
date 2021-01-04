from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func


db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    time_created = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    time_updated = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()