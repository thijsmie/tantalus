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

from psycopg2 import connect
from pq import PQ
import logging
import time
import traceback


class Worker:
    def __init__(self):
        self.conn_data = ""
        self.conn = None
        self.pq = None
        self.fn = {}
        self.app = None

    def init_app(self, app):
        self.app = app
        self.conn_data = app.config['SQLALCHEMY_DATABASE_URI']

    def ensure_pq(self):
        if self.conn is None:
            self.conn = connect(self.conn_data)
            self.pq = PQ(self.conn, table='_task_queue')
            self.pq.create()

    def task(self, fn):
        self.fn[fn.__name__] = fn
        def runner(*args, **kwargs):
            self.schedule(fn.__name__, *args, **kwargs)
        return runner

    def schedule(self, name, *args, **kwargs):
        data = {'name': name, 'args': args, 'kwargs': kwargs}
        self.ensure_pq()
        self.pq['main'].put(data)

    def work(self):
        self.ensure_pq() 
        queue = self.pq['main']
        while True:
            job = queue.get(timeout=60)
            if job is None:
                continue

            with self.app.test_request_context():
                config.refresh()
                try:
                    self.fn[job.data['name']](*job.data['args'], **job.data['kwargs'])
                    logging.info("Job has succeeded: " +
                        f"{job.data['name']}(" +
                        ", ".join(f"{i}" for i in job.data['args']) + ", "
                        ", ".join(f"{k}={v}" for k,v in job.data['kwargs'].items()) +
                        ")")
                    self.cleanup_sessions()
                except:
                    logging.critical(
                        "Job has failed: " +
                        f"{job.data['name']}(" +
                        ", ".join(f"{i}" for i in job.data['args']) + ", "
                        ", ".join(f"{k}={v}" for k,v in job.data['kwargs'].items()) +
                        ")\n" + traceback.format_exc()
                    )
                

    def cleanup_sessions(self):
        stale_time = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        Session.query.filter(Session.time_created < stale_time).delete()
        db.session.commit()

worker = Worker()

@worker.task
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


@worker.task
def conscribo_sync(transaction_ids):
    transactions = [get_or_none(id, Transaction) for id in transaction_ids]
    sync_transactions(transactions)


@worker.task
def run_create_snapshot(name):
    create_snapshot(name)


@worker.task
def advance_bookyear(yearcode):
    disable_logins()
    try:
        do_advance(yearcode)
    finally:
        enable_logins()
