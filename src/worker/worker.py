import datetime

from tantalus.snapshot.create import create_snapshot
from tantalus.api.actions.transaction import transaction_record

from tantalus_db.base import db
from tantalus_db.utility import get_or_none
from tantalus_db.models import Transaction, Session

from worker.invoice import make_invoice
from worker.sender import send_invoice
from worker.advancement import disable_logins, enable_logins, do_advance

from config import config

from ConscriboPyAPI.conscribo_sync import sync_transactions

from celery import Celery
from celery.schedules import crontab


celery = Celery(__name__, autofinalize=False)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Clear up stale sessions every 3 hours
    sender.add_periodic_task(
        datetime.timedelta(hours=3),
        cleanup_sessions.s(),
    )


@celery.task
def cleanup_sessions():
    stale_time = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    Session.query.filter(Session.time_created < stale_time).delete()
    db.session.commit()


@celery.task
def run_invoicing(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    relation = transaction.relation
    record = transaction_record(transaction)
    yearcode = config.yearcode

    def get_budget():
        after = Transaction.query.filter(
            Transaction.reference > transaction.reference, Transaction.relation == transaction.relation).all()
        return relation.budget + sum([t.total for t in after])

    if relation.has_budget:
        budget = get_budget()
    else:
        budget = None

    if relation.send_mail:
        pdf = make_invoice(transaction, record, relation, yearcode, budget)
        send_invoice(relation, transaction, pdf)


@celery.task
def conscribo_sync(transaction_ids):
    transactions = [get_or_none(id, Transaction) for id in transaction_ids]
    sync_transactions(transactions)


@celery.task
def run_create_snapshot(name):
    create_snapshot(name)


@celery.task
def advance_bookyear(yearcode):
    disable_logins()
    try:
        do_advance(yearcode)
    finally:
        enable_logins()
