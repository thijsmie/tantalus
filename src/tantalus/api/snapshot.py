from flask import render_template, request, redirect, url_for
from flask_login import login_required
from flask_weasyprint import HTML, render_pdf
from tantalus.api.actions.transaction import transaction_record

from tantalus_db.snapshot import Snapshot, TransactionSnapshot
from tantalus_db.paginator import Paginator

from tantalus.appfactory.auth import ensure_user_admin
from tantalus.api.routers import bp_snapshot as router
from tantalus.appfactory import flash

from tantalus.api.actions.snapshot import snapshot_group_excl_values, snapshot_group_values, \
    snapshot_service_excl_values, snapshot_service_values
from context import get_config
from worker.worker import run_create_snapshot

from datetime import datetime


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    pagination = Paginator(Snapshot.query.order_by(Snapshot.id.desc()), page, 20)
    return render_template('tantalus_snapshots.html', pagination=pagination)


@router.route('/view/<int:snapshot_id>')
@login_required
@ensure_user_admin
def show(snapshot_id):
    snapshot = Snapshot.query.get_or_404(snapshot_id)
    return render_template('tantalus_snapshot.html', snapshot=snapshot,
        group_values=snapshot_group_values(snapshot),
        group_excl_values=snapshot_group_excl_values(snapshot),
        service_values=snapshot_service_values(snapshot),
        service_excl_values=snapshot_service_excl_values(snapshot)
    )


@router.route('/create', methods=["POST"])
@login_required
@ensure_user_admin
def create():
    form = request.form or request.json

    if not form or not "name" in form:
        flash.danger("No data supplied")
        return redirect(url_for(".index"))
    
    run_create_snapshot.delay(form["name"])
    flash.success("Snapshot creation started, sit tight!")
    return redirect(url_for(".index"))


@router.route('/invoice/<int:transaction_id>.pdf')
@login_required
@ensure_user_admin
def pdf(transaction_id):
    transaction = TransactionSnapshot.query.get_or_404(transaction_id)
    relation = transaction.relation
    record = transaction_record(transaction)
    yearcode = transaction.snapshot.yearcode
    budget = transaction.budget

    html = render_template('invoice.html', transaction=transaction, record=record, relation=relation, yearcode=yearcode, budget=budget)
    return render_pdf(HTML(string=html))