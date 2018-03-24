from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError
from google.appengine.api import taskqueue

from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_transactions, ensure_user_relation, ensure_user_transaction

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Transaction, Product, Relation
from ndbextensions.paginator import Paginator
from ndbextensions.utility import get_or_none

from tantalus import bp_transaction as router
from actions.transaction import new_transaction, edit_transaction, transaction_record
from actions.relation import add_to_budget

from datetime import datetime


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_transactions
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(
        Transaction.query().order(-Transaction.deliverydate).order(-Transaction.lastedit), page, 20)
    return render_template('tantalus_transactions.html', pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_transactions
def indexjson():
    return jsonify(Transaction.query().fetch())


@router.route('/fromrelation/<string:relation_id>', defaults=dict(page=0))
@router.route('/fromrelation/<string:relation_id>/page/<int:page>')
@login_required
@ensure_user_relation
def showrelation(relation_id, page):
    if page < 0:
        page = 0

    relation = get_or_none(relation_id, Relation)
    if relation is None:
        return abort(404)

    pagination = Paginator(
        Transaction.query(Transaction.relation == relation.key).order(-Transaction.reference), page, 20,
        relation_id=relation_id
    )
    return render_template('tantalus_transactions.html', relation=relation, pagination=pagination)


@router.route('/fromrelation/<string:relation_id>.json')
@login_required
@ensure_user_transactions
def showrelationjson(relation_id):
    relation = get_or_none(relation_id, Relation)
    if relation is None:
        return abort(404)

    return jsonify(Transaction.query(Transaction.relation == relation.key).fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addtransaction():
    form = request.json
    if request.method == "POST":
        try:
            relation = get_or_none(form['relation'], Relation)
            if relation is None:
                raise BadValueError("Relation does not exist!")
            transaction = new_transaction(form)
            add_to_budget(relation.key, -transaction.total)

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.urlsafe()})

        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html',
                           products=Product.query(Product.hidden == False).fetch(),
                           relations=Relation.query().fetch())


@router.route('/edit/<string:transaction_id>', methods=["GET", "POST"])
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
            add_to_budget(transaction.relation, old_total - transaction.total)

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.urlsafe()})
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html', transaction=transaction,
                           products=Product.query(Product.hidden == False).fetch(),
                           relations=Relation.query().fetch())


@router.route('/view/<string:transaction_id>')
@login_required
@ensure_user_transaction
def showtransaction(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    return render_template('tantalus_transaction_viewer.html', **transaction_record(transaction))


@router.route('/resend/<string:transaction_id>')
@login_required
@ensure_user_admin
def resend(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    taskqueue.add(url='/invoice',
                  target='worker',
                  params={'transaction': transaction.key.urlsafe()})
    return redirect(url_for(".showtransaction", transaction_id=transaction_id))
    
    
@router.route('/history.json', methods=["POST"])
@login_required
@ensure_user_admin
def history():
    try:
        startdate = datetime.strptime(request.json["startdate"], "%Y-%m-%d").date()
        enddate = datetime.strptime(request.json["enddate"], "%Y-%m-%d").date()
    except:
        return abort(400)
        
    products = {}    
    transactions = Transaction.query(Transaction.deliverydate >= startdate).order(Transaction.deliverydate).fetch()
    for t in transactions:
        if (t.deliverydate > enddate):
            break
        for r in t.one_to_two:
            key = r.product.urlsafe()
            if key not in products:
                products[key] = {
                    "name": r.product.get().contenttype,
                    "buy": [],
                    "sell": []
                }
            products[key]["sell"] += [[r.amount, r.prevalue]]
        for r in t.two_to_one:
            key = r.product.urlsafe()
            if key not in products:
                products[key] = {
                    "name": r.product.get().contenttype,
                    "buy": [],
                    "sell": []
                }
            products[key]["buy"] += [[r.amount, r.prevalue]]
    return jsonify(products)
    
 
