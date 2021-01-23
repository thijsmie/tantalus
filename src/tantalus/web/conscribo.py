import json

from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from tantalus.appfactory.auth import ensure_user_admin

from tantalus_db.base import db
from tantalus_db.encode import jsonify
from tantalus_db.models import Transaction
from tantalus_db.conscribo import ConscriboConfig, ConscriboTransactionLink
from tantalus_db.utility import get_or_none

from tantalus.web.routers import bp_conscribo as router
from worker.worker import conscribo_sync


@router.route("/")
@login_required
@ensure_user_admin
def index():
    config = ConscriboConfig.get_config()
    transactionlinks = ConscriboTransactionLink.query.all()
    return render_template("tantalus_conscribo.html", config=config, transactionlinks=transactionlinks)


@router.route("/configure", methods=["POST"])
@login_required
@ensure_user_admin
def configure():
    data = request.form["config"]
    try:
        conf = json.loads(data)
    except:
        return jsonify({"error":"Incorrect json formatting"}, 400)

    ConscriboConfig.set_config(conf)
    db.session.commit()
    return redirect(url_for(".index"))


@router.route("/sync", methods=["POST"])
@login_required
@ensure_user_admin
def sync():
    data = request.form
    try:
        ids = [key for key in data if key != "_csrf_token"]
        trs = []
        for t in ids:
            l = get_or_none(t, ConscriboTransactionLink)
            if l is None:
                return jsonify({"message": "Unknown transactionlink {}".format(t)}, 400)
            else:
                trs.append(l.transaction)
        conscribo_sync([t.id for t in trs])
        db.session.commit()
    except (ValueError, KeyError, Exception):
        return jsonify({"message": "Bad data"}, 400)
    return redirect(url_for(".index"))
    
    
@router.route("/generate")
@login_required
@ensure_user_admin
def generate():
    transactions = Transaction.query.all()
    links = ConscriboTransactionLink.query.order_by(ConscriboTransactionLink.conscribo_reference).all()
    if links:
        next_id = links[-1].conscribo_reference + 1
    else:
        next_id = 1
        
    for t in transactions:
        if not t.conscribo_transaction:
            t.conscribo_transaction = ConscriboTransactionLink(
                pushed_revision=-1,
                conscribo_reference=next_id,
                transaction=t,
                bookdate=t.deliverydate
            )
            next_id += 1
            db.session.add(t.conscribo_transaction)
    db.session.commit()
    return jsonify({})


