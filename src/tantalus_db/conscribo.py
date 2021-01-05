from .base import Base, db
from sqlalchemy import Column, Text, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship

import json



class ConscriboConfig(Base):
    config = Column(Text, default="{}")

    @classmethod
    def get_config(cls):
        config = db.session.query.filter(cls).one_or_none()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()

        return json.loads(config.config)

    @classmethod
    def set_config(cls, config):
        config = db.session.query.filter(cls).one_or_none()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()

        config.config = json.dumps(config)


class ConscriboTransactionLink(Base):
    transaction_id = Column(Integer, ForeignKey('transaction.id'))
    transaction = relationship("Transaction", back_populates="conscribo_transaction")

    conscribo_reference = Column(Integer)
    pushed_revision = Column(Integer)
    bookdate = Column(Date)
    feedback = Column(Text, default="")

