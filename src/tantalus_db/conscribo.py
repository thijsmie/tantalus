from .base import Base, db
from sqlalchemy import Column, Text, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship

import json



class ConscriboConfig(Base):
    config = Column(Text, default="{}")

    @classmethod
    def get_config(cls):
        config = cls.query.one_or_none()
        if not config:
            config = cls()
            config.config = "{}"
            db.session.add(config)

        return json.loads(config.config)

    @classmethod
    def set_config(cls, config):
        config = cls.query.one_or_none()
        if not config:
            config = cls()
            config.config = "{}"
            db.session.add(config)

        config.config = json.dumps(config)
        db.session.commit()


class ConscriboTransactionLink(Base):
    transaction_id = Column(Integer, ForeignKey('transaction.id'))
    transaction = relationship("Transaction", back_populates="conscribo_transaction")

    conscribo_reference = Column(Integer)
    pushed_revision = Column(Integer)
    bookdate = Column(Date)
    feedback = Column(Text, default="")

