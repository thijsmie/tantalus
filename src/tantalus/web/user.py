from flask import render_template, request, abort
from flask_login import login_required

from tantalus.appfactory.auth import ensure_user_admin, new_user, update_password

from tantalus_db.base import db
from tantalus_db.encode import jsonify
from tantalus_db.models import User, Relation
from tantalus_db.paginator import Paginator
from tantalus_db.utility import get_or_none

from tantalus.web.routers import bp_user as router


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    if page < 0:
        page = 0

    query = User.query.order_by(User.username)
    pagination = Paginator(query, page, 20)
    return render_template('tantalus_users.html', pagination=pagination)


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def adduser():
    form = request.json

    if request.method == "POST":
        if form is None:
            abort(400)
        try:
            if len(User.query.filter(User.username == form['username']).all()):
                raise Exception("A user with this username already exists.")

            user = new_user(form['username'], form['password'], form.get('is_admin', False), form.get('relation', None),
                            form.get('viewstock', False), form.get('viewtransactions', False),
                            form.get('posaction', False), form.get('api', False))
            db.session.add(user)
            db.session.commit()
        except:
            return jsonify({"messages": ["Invalid data"]}, 403)
        return jsonify(user)
    return render_template('tantalus_user.html', relations=Relation.query.all())


@router.route('/edit/<string:user_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def edituser(user_id):
    form = request.json or request.form

    user = get_or_none(user_id, User)
    if user is None:
        return abort(404)

    if request.method == "POST":
        user.username = form.get('username', user.username)

        if 'password' in form:
            update_password(user, form['password'])

        if 'relation' in form:
            relation = get_or_none(form['relation'], Relation)
            if relation is None:
                abort(400)
            user.relation = relation

        user.right_admin = form.get('is_admin', user.right_admin)
        user.right_viewstock = form.get('viewstock', user.right_viewstock)
        user.right_viewalltransactions = form.get('viewtransactions', user.right_viewalltransactions)
        user.right_posaction = form.get('posaction', user.right_posaction)
        user.right_api = form.get('api', user.right_api)
        db.session.commit()
        return jsonify(user)

    return render_template('tantalus_user.html', user=user, relations=Relation.query.all())
