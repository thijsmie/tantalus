from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Mod
from ndbextensions.paginator import Paginator

from tantalus import bp_mod as router


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_admin
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(Mod.query().order(Mod.name), page, 20)
    return render_template('tantalus_mods.html', pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_admin
def indexjson():
    return jsonify(Mod.query().fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addmod():
    form = request.json

    if request.method == "POST":
        try:
            mod = Mod(
                name=form['name'],
                tag=form['tag'],
                description=form.get('description', ''),
                pre_add=form['pre_add'],
                multiplier=round(form['multiplier'], 2),
                post_add=form['post_add'],
                modifies=form['modifies'],
                divides=form['divides'],
                rounding=form['rounding']
            )
        except:
            return jsonify({"messsages": ["Improper datafields"]}, 402)

        try:
            mod.put()
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(mod)

    return render_template('tantalus_mod.html')


@router.route('/edit/<int:mod_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editmod(mod_id):
    form = request.json

    mod = Key("Mod", mod_id).get()
    if mod is None:
        abort(404)

    if request.method == "POST":
        try:
            mod.name = form.get('name', mod.name)
            mod.tag = form.get('tag', mod.tag)
            mod.description = form.get('description', mod.description)
            mod.pre_add = form.get('pre_add', mod.pre_add)
            mod.multiplier = form.get('multiplier', mod.multiplier)
            mod.post_add = form.get('post_add', mod.post_add)
            mod.modifies = form.get('modifies', mod.modifies)
            mod.divides = form.get('divides', mod.divides)
            mod.rounding = form.get('rounding', mod.rounding)
        except:
            return jsonify({"messsages": ["Improper datafields"]}, 402)

        try:
            mod.put()
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(mod)

    return render_template('tantalus_mod.html', mod=mod)
