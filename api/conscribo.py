from google.appengine.ext.ndb import Key, transactional
from google.appengine.ext.db import BadValueError
from google.appengine.api import taskqueue
import json

from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from appfactory.auth import ensure_user_admin

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Group, Relation, Transaction
from ndbextensions.conscribo import ConscriboConfig, ConscriboTransactionLink
from ndbextensions.utility import unlink, get_or_none

from tantalus import bp_conscribo as router


@router.route("/")
@login_required
@ensure_user_admin
def index():
    config = ConscriboConfig.get_config()
    defaultconf = ConscriboConfig.default_config()
    return render_template("tantalus_conscribo.html", config=config, defaultconf=defaultconf)


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
    return redirect(url_for(".index"))


@router.route("/transactions")
@login_required
@ensure_user_admin
def transactions():
    transactionlinks = ConscriboTransactionLink.query().fetch()
    return render_template("tantalus_conscribo_transactions.html", transactionlinks=transactionlinks)


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
        taskqueue.add(url="/csync", target="worker", params={"transactions": ",".join([t.urlsafe() for t in trs])})
    except (ValueError, KeyError, BadValueError):
        return jsonify({"message": "Bad data"}, 400)
    return redirect(url_for(".index"))
    
    
@router.route("/generate")
@login_required
@ensure_user_admin
def generate():
    transactions = Transaction.query().fetch()
    links = ConscriboTransactionLink.query().order(ConscriboTransactionLink.conscribo_reference).fetch()
    if links:
        next_id = links[-1].conscribo_reference + 1
    else:
        next_id = 1
        
    for t in transactions:
        for l in links:
            if l.transaction == t.key:
                break
        else:
            l = ConscriboTransactionLink(
                pushed_revision=-1,
                conscribo_reference=next_id,
                transaction=t.key,
                bookdate=t.deliverydate)
            next_id += 1
            l.put()
    return jsonify({})


