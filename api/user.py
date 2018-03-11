from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin, new_user, update_password

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import User, Relation
from ndbextensions.paginator import Paginator
from ndbextensions.utility import get_or_none

from tantalus import bp_user as router


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(User.query().order(User.username), page, 20)
    return render_template('tantalus_users.html', pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_admin
def indexjson():
    return jsonify(User.query().fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def adduser():
    form = request.json

    if request.method == "POST":
        if form is None:
            abort(400)
        try:
            if len(User.query(User.username == form['username']).fetch()):
                raise BadValueError("A user with this username already exists.")

            user = new_user(form['username'], form['password'], form.get('is_admin', False), form.get('relation', None),
                            form.get('viewstock', False), form.get('viewtransactions', False),
                            form.get('posaction', False))
            user.put()
        except (BadValueError, KeyError) as e:
            return jsonify({"messages": [e.message]}, 403)
        return jsonify(user)
    return render_template('tantalus_user.html', relations=Relation.query().fetch())


@router.route('/edit/<string:user_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def edituser(user_id):
    form = request.json or request.form

    user = get_or_none(user_id)
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
            user.relation = relation.key

        user.right_admin = form.get('is_admin', user.right_admin)
        user.right_viewstock = form.get('viewstock', user.right_viewstock)
        user.right_viewalltransactions = form.get('viewtransactions', user.right_viewalltransactions)
        user.right_posaction = form.get('posaction', user.right_posaction)

        user.put()
        return jsonify(user)

    return render_template('tantalus_user.html', user=user, relations=Relation.query().fetch())