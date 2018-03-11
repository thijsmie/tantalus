from google.appengine.ext.ndb import Key, transactional
from google.appengine.ext.db import BadValueError
from google.appengine.api import taskqueue

from flask import render_template, request, abort, redirect, url_for
from flask_login import login_required

from appfactory.auth import ensure_user_admin

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Group, Relation, Transaction
from ndbextensions.conscribo import ConscriboGroupLink, ConscriboRelationLink, ConscriboTransactionLink
from ndbextensions.utility import unlink, get_or_none

from tantalus import bp_conscribo as router


@router.route("/")
@login_required
@ensure_user_admin
def index():
    groups = Group.query().fetch()
    grouplinks = ConscriboGroupLink.query().fetch()
    relations = Relation.query().fetch()
    relationlinks = ConscriboRelationLink.query().fetch()
    return render_template("tantalus_conscribo.html",
                            groups=groups,
                            grouplinks=grouplinks,
                            relations=relations,
                            relationlinks=relationlinks)


@router.route("/link/group/add", methods=["POST"])
@login_required
@ensure_user_admin
def addgrouplink():
    data = request.form
    try:
        group = get_or_none(data["group"], Group)
        if group is None:
            return jsonify({}, 402)
        link = ConscriboGroupLink.query(ConscriboGroupLink.group == group.key).get()
        if link is not None:
            link.linked = int(data["linked"])
        else:    
            link = ConscriboGroupLink(group=group.key, linked=int(data["linked"]))
        link.put()
    except (ValueError, KeyError, BadValueError):
        return jsonify({}, 402)
    
    return redirect(url_for(".index"))


@router.route("/link/relation/add", methods=["POST"])
@login_required
@ensure_user_admin
def addrelationlink():
    data = request.form
    try:
        relation = get_or_none(data["relation"], Relation)
        if relation is None:
            return jsonify({}, 402)
        link = ConscriboRelationLink.query(ConscriboRelationLink.relation == relation.key).get()
        if link is not None:
            link.linked = int(data["linked"])
        else:            
            link = ConscriboRelationLink(relation=relation.key, linked=int(data["linked"]))
        link.put()
    except (ValueError, KeyError, BadValueError):
        return jsonify({}, 402)
    
    return redirect(url_for(".index"))


@router.route("/link/group/delete/<group_id>")
@login_required
@ensure_user_admin
def deletegrouplink(group_id):
    return unlink(group_id, ConscriboGroupLink)


@router.route("/link/relation/delete/<relation_id>")
@login_required
@ensure_user_admin
def deleterelationlink(relation_id):
    return unlink(relation_id, ConscriboRelationLink)


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


