import requests
import os
import sys

from context import get_config

from tantalus.api.actions.transaction import transaction_record
from tantalus_db.utility import get_or_none
from tantalus_db.models import Transaction

from worker.invoice import make_invoice
from worker.sender import send_invoice

from ConscriboPyAPI.conscribo_sync import sync_transactions

from celery import Celery


celery = Celery(__name__, autofinalize=False)


@celery.task
def make_invoice(transaction_id)
    transaction = get_or_none(transaction_id, Transaction)
    relation = transaction.relation.get()
    record = transaction_record(transaction)
    yearcode = get_config().yearcode

    def get_budget():
        after = Transaction.query.filter(
            Transaction.reference > transaction.reference, Transaction.relation == transaction.relation).all()
        return relation.budget + sum([t.total for t in after])

    if relation.has_budget:
        budget = get_budget()
    else:
        budget = None

    if relation.send_mail:
        pdf = make_invoice(record, relation, yearcode, budget)
        send_invoice(relation, transaction, pdf)


@celery.task
def conscribo_sync(transaction_ids):
    transactions = [get_or_none(key, Transaction) for id in transaction_ids]
    sync_transactions(transactions)
