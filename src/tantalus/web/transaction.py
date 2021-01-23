from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required
from flask_weasyprint import HTML, render_pdf

from tantalus_db.base import db
from tantalus_db.encode import jsonify
from tantalus_db.models import Transaction, Product, Relation
from tantalus_db.paginator import Paginator
from tantalus_db.utility import get_or_none

from tantalus.appfactory import flash
from tantalus.appfactory.auth import ensure_user_admin, ensure_user_transactions, ensure_user_relation, ensure_user_transaction
from tantalus.web.routers import bp_transaction as router
from tantalus.logic.transaction import new_transaction, edit_transaction, transaction_record

from config import config
from worker.worker import run_invoicing


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_transactions
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(
        Transaction.query.order_by(Transaction.deliverydate.desc(), Transaction.time_updated.desc()), page, 20)
    return render_template('tantalus_transactions.html', pagination=pagination)


@router.route('/fromrelation/<int:relation_id>', defaults=dict(page=0))
@router.route('/fromrelation/<int:relation_id>/page/<int:page>')
@login_required
@ensure_user_relation
def showrelation(relation_id, page):
    if page < 0:
        page = 0

    relation = get_or_none(relation_id, Relation)
    if relation is None:
        return abort(404)

    pagination = Paginator(
        Transaction.query.filter(Transaction.relation == relation).order_by(Transaction.informal_reference.desc()), page, 20,
        relation_id=relation_id
    )
    return render_template('tantalus_transactions.html', relation=relation, pagination=pagination)


@router.route('/fromrelation/<int:relation_id>.json')
@login_required
@ensure_user_transactions
def showrelationjson(relation_id):
    relation = Relation.query.get_or_404(relation_id)
    return jsonify(Transaction.query.filter(Transaction.relation == relation).all())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addtransaction():
    form = request.json

    if request.method == "POST":
        relation = Relation.query.get_or_404(int(form['relation']))
        transaction = new_transaction(form)
        relation.budget -= transaction.total
        run_invoicing(transaction.id)
        db.session.commit()
        return jsonify(transaction)

    return render_template('tantalus_transaction.html',
                           products=Product.query.filter(Product.discontinued == False).all(),
                           relations=Relation.query.all())


@router.route('/edit/<int:transaction_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def edittransaction(transaction_id):
    form = request.json

    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    if request.method == "POST":
        try:
            old_total = transaction.total
            transaction = edit_transaction(transaction, form)
            transaction.relation.budget += old_total - transaction.total
            run_invoicing(transaction.id)
            db.session.commit()
        except:
            return jsonify({"messages": ["Invalid data"]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html', transaction=transaction,
                           products=Product.query.filter(Product.discontinued == False).all(),
                           relations=Relation.query.all())


@router.route('/view/<int:transaction_id>')
@login_required
@ensure_user_transaction
def showtransaction(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    return render_template('tantalus_transaction_viewer.html', **transaction_record(transaction))


@router.route('/invoice/<int:transaction_id>')
@login_required
@ensure_user_transaction
def showinvoice(transaction_id):
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

    return render_template('invoice.html', transaction=transaction, record=record, relation=relation, yearcode=yearcode, budget=budget)


@router.route('/invoice/<int:transaction_id>.pdf')
@login_required
@ensure_user_transaction
def showinvoicepdf(transaction_id):
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

    html = render_template('invoice.html', transaction=transaction, record=record, relation=relation, yearcode=yearcode, budget=budget)
    return render_pdf(HTML(string=html))


@router.route('/resend/<int:transaction_id>')
@login_required
@ensure_user_admin
def resend(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    run_invoicing(transaction.id)
    flash.success("Resend queued (might take a few minutes to arrive).")

    return redirect(url_for(".showtransaction", transaction_id=transaction_id))
    
