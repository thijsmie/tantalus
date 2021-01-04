from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin

from tantalus_db.encode import jsonify
from tantalus_db.models import Relation
from tantalus_db.utility import get_or_none

from api.common import common_collection
from api.actions.relation import new_relation

from tantalus.api.routers import bp_relation as router


common_collection(
    router, 
    ensure_user_admin,
    Relation.query.order_by(Relation.name), 
    'tantalus_relations.html'
)


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addrelation():
    form = request.json

    if request.method == "POST":
        try:
            new_relation(form)
        except:
            return jsonify({"messages": ["Invalid data"]}, 403)
        return jsonify(relation)
    return render_template('tantalus_relation.html')


@router.route('/edit/<int:relation_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editrelation(relation_id):
    form = request.json or request.form

    relation = Relation.query.get_or_404(relation_id)

    if request.method == "POST":
        edit_relation(relation, form)

    return render_template('tantalus_relation.html', relation=relation)
