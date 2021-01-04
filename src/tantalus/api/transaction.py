from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_transactions, ensure_user_relation, ensure_user_transaction

from tantalus_db.encode import jsonify
from tantalus_db.models import Transaction, Product, Relation
from tantalus_db.paginator import Paginator
from tantalus_db.utility import get_or_none

from tantalus.api.routers import bp_transaction as router
from actions.transaction import new_transaction, edit_transaction, transaction_record

from datetime import datetime


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


@router.route('.json')
@login_required
@ensure_user_transactions
def indexjson():
    return jsonify(Transaction.query.all())


@router.route('.cjson')
@login_required
@ensure_user_transactions
def indexconvinientjson():
    return jsonify([transaction_record(t) for t in Transaction.query.all()])


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

        try:
            transaction = new_transaction(form)
            relation.budget -= transaction.total

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.urlsafe()})
        except:
            return jsonify({"messages": ["Invalid data"]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html',
                           products=Product.query.filter(Product.hidden == False).all(),
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

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.urlsafe()})
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html', transaction=transaction,
                           products=Product.query.filter(Product.hidden == False).all(),
                           relations=Relation.query.all())


@router.route('/view/<int:transaction_id>')
@login_required
@ensure_user_transaction
def showtransaction(transaction_id):
    transaction = get_or_none(transaction_id, Transaction)
    if transaction is None:
        return abort(404)

    return render_template('tantalus_transaction_viewer.html', **transaction_record(transaction))


@router.route('/resend/<int:transaction_id>')
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
    transactions = Transaction.query.filter(Transaction.deliverydate >= startdate).order_by(Transaction.deliverydate).all()
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
    
 
