""" Copy certain models to take a read-only snapshot of the database """    
from .base import db, Base

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr



class Snapshot(Base):
    name = Column(String(200), nullable=False, default="")
    yearcode = Column(Integer, nullable=False)

    relations = relationship('RelationSnapshot', order_by="RelationSnapshot.name")
    btwtypes = relationship('BtwTypeSnapshot')
    products = relationship('ProductSnapshot', order_by="ProductSnapshot.contenttype")
    transactions = relationship('TransactionSnapshot', order_by="TransactionSnapshot.reference")


class SnapshotBase(Base):
    __abstract__ = True

    @declared_attr
    def snapshot_id(cls):
        return Column(Integer, ForeignKey('snapshot.id'), index=True, nullable=False)
    
    @declared_attr
    def snapshot(cls):
        return relationship('Snapshot')

class RelationSnapshot(SnapshotBase):
    name = Column(String(200), nullable=False)
    budget = Column(Integer, default=0)

    transactions = relationship('TransactionSnapshot', back_populates='relation')

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "name": self.name,
            "budget": self.budget
        }


class BtwTypeSnapshot(SnapshotBase):
    name = Column(String, nullable=False)
    percentage = Column(Integer, nullable=False)

    products = relationship("ProductSnapshot", back_populates="btwtype")
    transaction_lines = relationship('TransactionLineSnapshot', back_populates="btwtype")
    service_lines = relationship('ServiceLineSnapshot', back_populates="btwtype")

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "name": self.name,
            "percentage": self.percentage
        }

        
class GroupSnapshot(SnapshotBase):
    name = Column(String, nullable=False)

    products = relationship("ProductSnapshot", back_populates="group")
        
    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "name": self.name
        }


class ProductSnapshot(SnapshotBase):
    contenttype = Column(String, nullable=False, index=True)
    tag = Column(String, nullable=False, default="")
    value = Column(Integer, nullable=False, default=0)
    amount = Column(Integer, nullable=False, default=0)
    
    discontinued = Column(Boolean, nullable=False, default=False)
    group_id = Column(Integer, ForeignKey('groupsnapshot.id'), nullable=False)
    group = relationship("GroupSnapshot", back_populates="products")
    
    btwtype_id = Column(Integer, ForeignKey('btwtypesnapshot.id'), nullable=False)
    btwtype = relationship("BtwTypeSnapshot", back_populates="products")

    transaction_lines = relationship('TransactionLineSnapshot', back_populates="product")

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "contenttype": self.contenttype,
            "tag": self.tag,
            "value": self.value,
            "amount": self.amount,
            "discontinued": self.discontinued,
            "group": self.group_id,
            "btwtype": self.btwtype_id
        }


class TransactionLineSnapshot(SnapshotBase):
    transaction_id_one_to_two = Column(Integer, ForeignKey('transactionsnapshot.id'), index=True, nullable=True)
    transaction_one_to_two = relationship('TransactionSnapshot', back_populates='one_to_two', foreign_keys=[transaction_id_one_to_two])

    transaction_id_two_to_one = Column(Integer, ForeignKey('transactionsnapshot.id'), index=True, nullable=True)
    transaction_two_to_one = relationship('TransactionSnapshot', back_populates='two_to_one', foreign_keys=[transaction_id_two_to_one])

    product_id = Column(Integer, ForeignKey('productsnapshot.id'))
    product = relationship('ProductSnapshot', back_populates='transaction_lines')
    
    prevalue = Column(Integer, nullable=False)
    value = Column(Integer, nullable=False)
    
    btwtype_id = Column(Integer, ForeignKey('btwtypesnapshot.id'), nullable=False)
    btwtype = relationship("BtwTypeSnapshot", back_populates="transaction_lines")
    
    amount = Column(Integer, nullable=False)

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "product": self.product_id,
            "prevalue": self.prevalue,
            "value": self.value,
            "btwtype": self.btwtype_id,
            "amount": self.amount
        }


class ServiceLineSnapshot(SnapshotBase):
    transaction_id = Column(Integer, ForeignKey('transactionsnapshot.id'), index=True, nullable=True)
    transaction = relationship('TransactionSnapshot', back_populates='services')

    service = Column(String(200), nullable=False)
    value = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    
    btwtype_id = Column(Integer, ForeignKey('btwtypesnapshot.id'), nullable=False)
    btwtype = relationship("BtwTypeSnapshot", back_populates="service_lines")

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
            "service": self.service,
            "value": self.value,
            "btwtype": self.btwtype_id,
            "amount": self.amount
        }


class TransactionSnapshot(SnapshotBase):
    reference = Column(Integer, index=True, nullable=False)
    informal_reference = Column(Integer, index=True, nullable=False)
    revision = Column(Integer, default=0, nullable=False)
    deliverydate = Column(Date, nullable=False)
    processeddate = Column(Date, nullable=False)
    description = Column(Text, default="")

    relation_id = Column(Integer, ForeignKey('relationsnapshot.id'), index=True, nullable=False)
    relation = relationship("RelationSnapshot", back_populates="transactions")

    one_to_two = relationship('TransactionLineSnapshot', foreign_keys=[TransactionLineSnapshot.transaction_id_one_to_two])
    two_to_one = relationship('TransactionLineSnapshot', foreign_keys=[TransactionLineSnapshot.transaction_id_two_to_one])
    services = relationship('ServiceLineSnapshot', back_populates='transaction')

    total = Column(Integer, nullable=False, default=0)
    two_to_one_has_btw = Column(Boolean, nullable=False, default=False)
    two_to_one_btw_per_row = Column(Boolean, nullable=False, default=False)

    conscribo_reference = Column(Integer, nullable=True)
    budget = Column(Integer, nullable=True)

    def dict(self):
        return {
            "id": self.id,
            "snapshot": self.snapshot,
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
            "two_to_one_btw_per_row": self.two_to_one_btw_per_row,
            "conscribo_reference": self.conscribo_reference
        }
