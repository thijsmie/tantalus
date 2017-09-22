from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError
from google.appengine.api import taskqueue

from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_transactions, ensure_user_relation, ensure_user_transaction

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Transaction, Product, Mod, Relation, TypeGroup
from ndbextensions.paginator import Paginator

from tantalus import bp_transaction as router
from actions.transaction import new_transaction, edit_transaction, transaction_record
from actions.relation import add_to_budget


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


@router.route('/fromrelation/<int:relation_id>', defaults=dict(page=0))
@router.route('/fromrelation/<int:relation_id>/page/<int:page>')
@login_required
@ensure_user_relation
def showrelation(relation_id, page):
    if page < 0:
        page = 0

    pagination = Paginator(
        Transaction.query(
            Transaction.relation == Key('Relation', relation_id, parent=TypeGroup.relation_ancestor())).order(
            -Transaction.reference), page, 20,
        relation_id=relation_id)
    return render_template('tantalus_transactions.html',
                           relation=Key('Relation', relation_id, parent=TypeGroup.relation_ancestor()).get(),
                           pagination=pagination)


@router.route('/fromrelation/<int:relation>.json')
@login_required
@ensure_user_transactions
def showrelationjson(relation):
    return jsonify(Transaction.query(
        Transaction.relation == Key('Relation', relation, parent=TypeGroup.relation_ancestor())).fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addtransaction():
    form = request.json
    ref = None

    if request.method == "POST":
        try:
            relation_key = Key("Relation", int(form['relation']), parent=TypeGroup.relation_ancestor())
            relation = relation_key.get()
            if relation is None:
                raise BadValueError("Relation does not exist!")
            transaction = new_transaction(form)
            add_to_budget(relation_key, -transaction.total)

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.id()})

        except BadValueError as e:
            if ref is not None:  # free number of transaction
                ref.key.delete()
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html',
                           products=Product.query(Product.hidden == False).fetch(),
                           mods=Mod.query().fetch(),
                           relations=Relation.query().fetch())


@router.route('/edit/<int:transaction_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def edittransaction(transaction_id):
    form = request.json

    transaction = Key("Transaction", transaction_id, parent=TypeGroup.transaction_ancestor()).get()

    if transaction is None:
        return abort(404)

    if request.method == "POST":
        try:
            old_total = transaction.total
            transaction = edit_transaction(transaction, form)
            add_to_budget(transaction.relation, old_total - transaction.total)

            taskqueue.add(url='/invoice',
                          target='worker',
                          params={'transaction': transaction.key.id()})
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(transaction)

    return render_template('tantalus_transaction.html', transaction=transaction,
                           products=Product.query(Product.hidden == False).fetch(),
                           mods=Mod.query().fetch(),
                           relations=Relation.query().fetch())


@router.route('/view/<int:transaction_id>')
@login_required
@ensure_user_transaction
def showtransaction(transaction_id):
    transaction = Key("Transaction", transaction_id, parent=TypeGroup.transaction_ancestor()).get()

    if transaction is None:
        return abort(404)

    return render_template('tantalus_transaction_viewer.html', **transaction_record(transaction))


@router.route('/resend/<int:transaction_id>')
@login_required
@ensure_user_admin
def resend(transaction_id):
    transaction = Key("Transaction", transaction_id, parent=TypeGroup.transaction_ancestor()).get()

    if transaction is None:
        return abort(404)

    taskqueue.add(url='/invoice',
                  target='worker',
                  params={'transaction': transaction.key.id()})
    return redirect(url_for(".showtransaction", transaction_id=transaction_id))
