from .base import Base, db

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Date, DateTime, Text
from sqlalchemy.orm import relationship, validates

import datetime


class Referencing(Base):
    counter = Column(Integer, default=1)

    @classmethod
    def get_reference(cls):
        inst = cls.query.first()
        if not inst:
            inst = cls()
            inst.counter = 1
            db.session.add(inst)

        reference = inst.counter
        inst.counter += 1

        return reference


class Relation(Base):
    name = Column(String(200), nullable=False, unique=True)
    budget = Column(Integer, default=0)

    has_budget = Column(Boolean, nullable=False)
    send_mail = Column(Boolean, nullable=False)
    numbered_reference = Column(Boolean, nullable=False, default=True)

    email = Column(String(512), nullable=False, default="")
    address = Column(String(512), nullable=False, default="")

    users = relationship('User', back_populates='relation')
    transactions = relationship('Transaction', back_populates='relation')

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 1
        return name

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "budget": self.budget,
            "has_budget": self.has_budget,
            "send_mail": self.send_mail,
            "numbered_reference": self.numbered_reference,
            "email": self.email,
            "address": self.address,
        }


class BtwType(Base):
    name = Column(String, nullable=False)
    percentage = Column(Integer, nullable=False)

    products = relationship("Product", back_populates="btwtype")
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

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "percentage": self.percentage
        }

        
class Group(Base):
    name = Column(String, nullable=False)

    products = relationship("Product", back_populates="group")

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 4
        return name
        
    def dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


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
            product=self,
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

    def dict(self):
        return {
            "id": self.id,
            "contenttype": self.contenttype,
            "tag": self.tag,
            "value": self.value,
            "amount": self.amount,
            "hidden": self.hidden,
            "group": self.group_id,
            "btwtype": self.btwtype_id
        }


class TransactionLine(Base):
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

    def dict(self):
        return {
            "id": self.id,
            "product": self.product_id,
            "prevalue": self.prevalue,
            "value": self.value,
            "btwtype": self.btwtype_id,
            "amount": self.amount
        }


class ServiceLine(Base):
    transaction_id = Column(Integer, ForeignKey('transaction.id'), index=True, nullable=True)
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

    def dict(self):
        return {
            "id": self.id,
            "service": self.service,
            "value": self.value,
            "btwtype": self.btwtype_id,
            "amount": self.amount
        }


class Transaction(Base):
    reference = Column(Integer, index=True, nullable=False)
    informal_reference = Column(Integer, index=True, nullable=False)
    revision = Column(Integer, default=0, nullable=False)
    deliverydate = Column(Date, nullable=False)
    processeddate = Column(Date, nullable=False)
    description = Column(Text, default="")

    relation_id = Column(Integer, ForeignKey('relation.id'), index=True, nullable=False)
    relation = relationship("Relation", back_populates="transactions")

    one_to_two = relationship('TransactionLine', lazy='joined', foreign_keys=[TransactionLine.transaction_id_one_to_two])
    two_to_one = relationship('TransactionLine', lazy='joined', foreign_keys=[TransactionLine.transaction_id_two_to_one])
    services = relationship('ServiceLine', back_populates='transaction', lazy='joined')

    total = Column(Integer, nullable=False, default=0)
    two_to_one_has_btw = Column(Boolean, nullable=False, default=False)
    two_to_one_btw_per_row = Column(Boolean, nullable=False, default=False)

    conscribo_transaction = relationship("ConscriboTransactionLink", back_populates="transaction", uselist=False)

    def dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "informal_reference": self.informal_reference,
            "revision": self.revision,
            "deliverydate": self.deliverydate,
            "processeddate": self.processeddate,
            "description": self.description,
            "relation": self.relation_id,
            "one_to_two": [row.dict() for row in self.one_to_two],
            "two_to_one": [row.dict() for row in self.two_to_one],
            "services": [row.dict() for row in self.services],
            "total": self.total,
            "two_to_one_has_btw": self.two_to_one_has_btw,
            "two_to_one_btw_per_row": self.two_to_one_btw_per_row
        }


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

    def dict(self):
        return {
            "username": self.username,
            "relation": self.relation_id,
            "right_admin": self.right_admin,
            "right_viewstock": self.right_viewstock,
            "right_viewalltransactions": self.right_viewalltransactions,
            "right_posaction": self.right_posaction
        }