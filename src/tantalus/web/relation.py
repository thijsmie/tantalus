from flask import render_template, request, abort
from flask_login import login_required

from tantalus.appfactory.auth import ensure_user_admin

from tantalus_db.base import db
from tantalus_db.encode import jsonify
from tantalus_db.models import Relation
from tantalus_db.paginator import Paginator
from tantalus_db.utility import get_or_none

from tantalus.web.routers import bp_relation as router
from tantalus.logic.relation import new_relation, edit_relation


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    if page < 0:
        page = 0

    query = Relation.query.order_by(Relation.name)
    pagination = Paginator(query, page, 20)
    return render_template('tantalus_relations.html', pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_admin
def indexjson():
    query = Relation.query.order_by(Relation.name)
    return jsonify(query.all())

@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addrelation():
    form = request.json

    if request.method == "POST":
        try:
            relation = new_relation(form)
            db.session.commit()
        except:
            return jsonify({"messages": ['Invalid data']}, 403)
        return jsonify(relation)
    return render_template('tantalus_relation.html')


@router.route('/edit/<int:relation_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editrelation(relation_id):
    form = request.json or request.form

    relation = get_or_none(relation_id, Relation)
    if relation is None:
        return abort(404)

    if request.method == "POST":
        edit_relation(relation, form)
        db.session.commit()
        return jsonify(relation)

    return render_template('tantalus_relation.html', relation=relation)