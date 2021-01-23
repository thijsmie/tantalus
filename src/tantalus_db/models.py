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

    filters = classmethod(dict)


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
        assert percentage >= 0
        return percentage

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "percentage": self.percentage
        }

    filters = classmethod(dict)
        
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

    filters = classmethod(dict)

class Product(Base):
    contenttype = Column(String, nullable=False, index=True)
    tag = Column(String, nullable=False, default="")
    value = Column(Integer, nullable=False, default=0)
    amount = Column(Integer, nullable=False, default=0)
    
    discontinued = Column(Boolean, nullable=False, default=False)
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
            "discontinued": self.discontinued,
            "group": self.group_id,
            "btwtype": self.btwtype_id
        }

    filters = classmethod(dict)

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

    filters = classmethod(dict)

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

    filters = classmethod(dict)

class Transaction(Base):
    reference = Column(Integer, index=True, nullable=False)
    informal_reference = Column(Integer, index=True, nullable=False)
    revision = Column(Integer, default=0, nullable=False)
    deliverydate = Column(Date, nullable=False)
    processeddate = Column(Date, nullable=False)
    description = Column(Text, default="")

    relation_id = Column(Integer, ForeignKey('relation.id'), index=True, nullable=False)
    relation = relationship("Relation", back_populates="transactions")

    one_to_two = relationship('TransactionLine', cascade="all, delete-orphan", foreign_keys=[TransactionLine.transaction_id_one_to_two])
    two_to_one = relationship('TransactionLine', cascade="all, delete-orphan", foreign_keys=[TransactionLine.transaction_id_two_to_one])
    services = relationship('ServiceLine', cascade="all, delete-orphan", back_populates='transaction')

    total = Column(Integer, nullable=False, default=0)
    two_to_one_has_btw = Column(Boolean, nullable=False, default=False)
    two_to_one_btw_per_row = Column(Boolean, nullable=False, default=False)

    conscribo_transaction = relationship("ConscriboTransactionLink", cascade="all, delete-orphan", back_populates="transaction", uselist=False)

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

    @classmethod
    def filters(cls):
        return {
            "id": cls.id,
            "reference": cls.reference,
            "informal_reference": cls.informal_reference,
            "revision": cls.revision,
            "deliverydate": cls.deliverydate,
            "processeddate": cls.processeddate,
            "description": cls.description,
            "relation": cls.relation_id,
            "total": cls.total,
            "two_to_one_has_btw": cls.two_to_one_has_btw,
            "two_to_one_btw_per_row": cls.two_to_one_btw_per_row
        }

class User(Base):
    username = Column(String(200), index=True, nullable=False)
    passhash = Column(Text)

    relation_id = Column(Integer, ForeignKey('relation.id'))
    relation = relationship('Relation', back_populates='users')

    right_admin = Column(Boolean, nullable=False, default=False)
    right_viewstock = Column(Boolean, nullable=False, default=False)
    right_viewalltransactions = Column(Boolean, nullable=False, default=False)
    right_posaction = Column(Boolean, nullable=False, default=False)
    right_api = Column(Boolean, nullable=False, default=False)

    @validates('username')
    def validate_username(self, key, username):
        assert len(username) >= 4
        return username

    def dict(self):
        return {
            "username": self.username,
            "relation": self.relation_id,
            "right_admin": self.right_admin,
            "right_viewstock": self.right_viewstock,
            "right_viewalltransactions": self.right_viewalltransactions,
            "right_posaction": self.right_posaction
        }

    filters = classmethod(dict)

class Session(Base):
    session = Column(String(128), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', lazy='joined')

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


class PosEndpoint(Base):
    name = Column(String)
    relation_id = Column(Integer, ForeignKey('relation.id'))
    relation = relationship('Relation')

    sales = relationship('PosSale', back_populates="posendpoint")

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 1
        return name

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "relation": self.relation_id
        }
    filters = classmethod(dict)


class PosProduct(Base):
    name = Column(String, nullable=False)
    discontinued = Column(Boolean, nullable=False, default=False)

    product_id = Column(Integer, ForeignKey('product.id'), nullable=True)
    product = relationship('Product')

    service = Column(String, nullable=True)
    service_btw_id = Column(Integer, ForeignKey('btwtype.id'), nullable=True)
    service_btw = relationship('BtwType')
    service_price = Column(Integer, nullable=True)

    scan_id = Column(String, default="")
    keycode = Column(String, default="")

    sales = relationship('PosSale', back_populates="posproduct")

    @property
    def is_service(self):
        return self.product == None

    @validates('name')
    def validate_name(self, key, name):
        assert len(name) >= 1
        return name

    def dict(self):
        dc = {
            "id": self.id,
            "name": self.name,
            "discontinued": self.discontinued,
            "scan_id": self.scan_id,
            "keycode": self.keycode,
            "is_service": self.is_service
        }
        if self.is_service:
            dc.update({
                "service": self.service,
                "btwtype": self.service_btw_id,
                "price": self.service_price
            })
        else:
            dc.update({
                "product": self.product_id,
                "price": self.product.value
            })
        return dc

    @classmethod
    def filters(cls):
        return {
            "id": cls.id,
            "name": cls.name,
            "discontinued": cls.discontinued,
            "scan_id": cls.scan_id,
            "keycode": cls.keycode,
            "service": cls.service,
            "btwtype": cls.service_btw_id,
            "price": cls.service_price,
            "product": cls.product_id
        }

    
class PosSale(Base):
    # Note: the price and btw need to be tracked in the sale to make sure that price
    #       and btw changes have no influence on the past
    posendpoint_id = Column(Integer, ForeignKey('posendpoint.id'), nullable=False)
    posendpoint = relationship("PosEndpoint", back_populates="sales")
    posproduct_id = Column(Integer, ForeignKey('posproduct.id'), nullable=False)
    posproduct = relationship("PosProduct", back_populates="sales")
    amount = Column(Integer, nullable=False, default=1)
    unit_price = Column(Integer, nullable=False)
    btwtype_id = Column(Integer, ForeignKey('btwtype.id'), nullable=True)
    btwtype = relationship('BtwType')
    processed = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User')

    def dict(self):
        return {
            "id": self.id,
            "posendpoint": self.posendpoint_id,
            "posproduct": self.posproduct_id,
            "amount": self.amount,
            "unit_price": self.unit_price,
            "btwtype": self.btwtype_id,
            "processed": self.processed,
            "user": self.user_id
        }

    filters = classmethod(dict)