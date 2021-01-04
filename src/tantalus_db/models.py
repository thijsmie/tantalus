from .base import Base, db

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Date, DateTime
from sqlalchemy.orm import relationship, validates

import datetime


class Referencing(Base):
    counter = Column(Integer, default=1)

    @classmethod
    def get_reference(cls):
        inst = cls.query.first_or_none()
        if not inst:
            inst = cls()
            db.session.add(inst)

        reference = cls.counter
        cls.counter += 1

        return reference


class Relation(Base):
    name = Column(String(200), nullable=False, unique=True)
    budget = Column(Integer, default=0)

    has_budget = Column(Boolean, nullable=False)
    send_mail = Column(Boolean, nullable=False)
    numbered_reference = Column(Boolean, nullable=False, default=True)

    email = Column(String(512), nullable=False, default="")
    address = Column(String(512), nullable=False, default="")

    users = relation('User', back_populates='relation')

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 1
        return name


class BtwType(Base):
    name = Column(String, nullable=False)
    percentage = Column(Integer, nullable=False)

    products = relationship("Product", back_populates="group")
    transaction_lines = relationship('TransactionLine', back_populates="btwtype")
    service_lines = relationship('ServiceLine', back_populates="btwtype")

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 1
        return name

    @validates('percentage')
    def validate_percenctage(self, key, percentage):
        assert percentage > 0
        return percentage

        
class Group(Base):
    name = Column(String, nullable=False)

    products = relationship("Product", back_populates="group")

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 4
        return name


class Product(Base):
    contenttype = Column(String, nullable=False, index=True)
    tag = Column(String, nullable=False, default="")
    value = Column(Integer, nullable=False, default=0)
    amount = Column(Integer, nullable=False, default=0)
    
    hidden = Column(Boolean, nullable=False, default=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", back_populates="products")
    
    btwtype_id = Column(Integer, ForeignKey('btwtype.id'), nullable=False)
    btwtype = relationship("BtwType", back_populates="products")

    transaction_lines = relationship('TransactionLine', back_populates="product")

    @validates('contenttype')
    def validate_contenttype(self, key, contenttype):
        assert len(contenttype) >= 4
        return contenttype

    def take(self, amount):
        assert amount > 0
        self.amount -= amount
     
        return TransactionLine(
            product=self.key,
            amount=amount,
            prevalue=amount*self.value,
            value=amount*self.value,
            btwtype=self.btwtype
        )

    def give(self, container_or_amount):
        if type(container_or_amount) == int:
            amount = container_or_amount
        else:
            amount = container_or_amount.amount

        assert amount > 0
        self.amount += amount


class TransactionLine(Base):
    __abstract__ = True

    transaction_id_one_to_two = Column(Integer, ForeignKey('transaction.id'), index=True, nullable=True)
    transaction_one_to_two = relationship('Transaction', back_populates='one_to_two', foreign_keys=[transaction_id_one_to_two])

    transaction_id_two_to_one = Column(Integer, ForeignKey('transaction.id'), index=True, nullable=True)
    transaction_two_to_one = relationship('Transaction', back_populates='two_to_one', foreign_keys=[transaction_id_two_to_one])

    product_id = Column(Integer, ForeignKey('product.id'))
    product = relationship('Product', back_populates='transaction_lines')
    
    prevalue = Column(Integer, nullable=False)
    value = Column(Integer, nullable=False)
    
    btwtype_id = Column(Integer, ForeignKey('btwtype.id'), nullable=False)
    btwtype = relationship("BtwType", back_populates="transaction_lines")
    
    amount = Column(Integer, nullable=False)
    
    conscribo_transaction = relationship("ConscriboTransactionLink", back_populates="transaction", uselist=False)

    def take(self, amount):
        assert amount > 0
        assert amount < self.amount

        # Note: this rounding is always precise
        value = self.value * amount // self.amount
        
        # TODO CRITICAL why does this take not modify this line?

        return TransactionLine(
            product=self.product,
            amount=amount,
            prevalue=value,
            btwtype=self.btwtype
        )


class ServiceLine(Base):
    transaction_id = Column(Integer, ForeignKey('transaction.id'), index=True, nullable=False)
    transaction = relationship('Transaction', back_populates='services')

    service = Column(String(200), nullable=False)
    value = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    
    btwtype_id = Column(Integer, ForeignKey('btwtype.id'), nullable=False)
    btwtype = relationship("BtwType", back_populates="service_lines")

    @validates('service')
    def validate_service(self, key, service):
        assert len(service) >= 1
        return service


class Transaction(Base):
    reference = Column(Integer, index=True, nullable=False)
    informal_reference = Column(Integer, index=True, nullable=False)
    revision = Column(Integer, default=0, nullable=False)
    deliverydate = Column(Date, nullable=False)
    processeddate = Column(Date, nullable=False)
    description = Column(Text, default="")

    relation_id = Column(Integer, ForeignKey('transaction.id'), index=True, nullable=False)
    relation = relationship("Relation", back_populates="transactions")

    one_to_two = relationship('TransactionLine', lazy='joined')
    two_to_one = relationship('TransactionLine', lazy='joined')
    services = relationship('ServiceLine', back_populates='transaction', lazy='joined')

    total = Column(Integer, nullable=False, default=0)
    two_to_one_has_btw = Column(Boolean, nullable=False, default=False)
    two_to_one_btw_per_row = Column(Booleanh, nullable=False, default=False)


class User(Base):
    session = Column(String(256), index=True, nullable=True)

    username = Column(String(200), index=True, nullable=False)
    passhash = Column(Text)

    relation_id = Column(Integer, ForeignKey('relation.id'))
    relation = relationship('Relation', back_populates='users')

    right_admin = Column(Boolean, nullable=False, default=False)
    right_viewstock = Column(Boolean, nullable=False, default=False)
    right_viewalltransactions = Column(Boolean, nullable=False, default=False)
    right_posaction = Column(Boolean, nullable=False, default=False)

    @validates('username')
    def validate_username(self, key, username):
        assert len(username) >= 4
        return username

    # Flask-Login required functionality

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.session
