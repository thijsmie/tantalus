"""
Utilities for advancing bookyear
"""
from tantalus_db.base import db
from tantalus_db.models import PosSale, Session, Transaction, Referencing, Product, PosProduct
from tantalus_db.config import Setting
from tantalus_db.utility import transactional

from tantalus.snapshot.create import create_snapshot

from config import config


@transactional
def disable_logins():
    setting = Setting.query.filter(Setting.name == "nologin").one()
    setting.value = "true"
    Session.query.delete()


@transactional
def enable_logins():
    setting = Setting.query.filter(Setting.name == "nologin").one()
    setting.value = "false"


@transactional
def do_advance(yearcode):
    # Create a snapshot of the final tally
    create_snapshot("End of year")

    # We have to actually load the objects to get cascading deletes
    for t in Transaction.query.all():
        db.session.delete(t)
    for t in PosSale.query.filter(PosSale.processed == True).all():
        db.session.delete(t)

    # No need for cascades with posproduct and product
    # Note, if there are any sales depending on the posproduct this will fail
    # That is intended, user error
    Product.query.filter(Product.discontinued == True).delete()
    PosProduct.query.filter(PosProduct.discontinued == True).delete()

    # Advance yearcode and manually update config to reflect that within this transaction
    setting = Setting.query.filter(Setting.name == "yearcode").one()
    setting.value = yearcode
    config.yearcode = yearcode

    # Reset the reference counter by deleting it (It will be recreated on the first transaction to be added)
    Referencing.query.delete()

    # Create a snapshot of the begin state
    create_snapshot("Start of year")

