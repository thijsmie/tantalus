from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Relation
from ndbextensions.paginator import Paginator
from ndbextensions.utility import get_or_none

from tantalus import bp_relation as router


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(Relation.query().order(Relation.name), page, 20)
    return render_template('tantalus_relations.html', pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_admin
def indexjson():
    return jsonify(Relation.query().fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addrelation():
    form = request.json

    if request.method == "POST":
        if form is None:
            abort(400)
        try:
            if len(Relation.query(Relation.name == form['name']).fetch()):
                raise BadValueError("A relation with this name already exists.")

            relation = Relation(
                name=form['name'],
                budget=form['budget'],
                email=form['email'],
                has_budget=form['has_budget'],
                send_mail=form['send_mail'],
                address=form['address']
            ).put()
        except (BadValueError, KeyError) as e:
            return jsonify({"messages": [e.message]}, 403)
        return jsonify(relation)
    return render_template('tantalus_relation.html')


@router.route('/edit/<string:relation_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editrelation(relation_id):
    form = request.json or request.form

    relation = get_or_none(relation_id, Relation)
    if relation is None:
        return abort(404)

    if request.method == "POST":
        relation.name = form.get('name', relation.name)
        relation.email = form.get('email', relation.email)
        relation.budget = form.get('budget', relation.budget)
        relation.has_budget = form.get('has_budget', relation.has_budget)
        relation.send_mail = form.get('send_mail', relation.send_mail)
        relation.address = form.get('address', relation.address)
        relation.put()
        return jsonify(relation)

    return render_template('tantalus_relation.html', relation=relation)

