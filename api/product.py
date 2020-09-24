from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_stock

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Product, Group, BtwType
from ndbextensions.paginator import Paginator
from ndbextensions.utility import get_or_none

from tantalus import bp_product as router
from collections import defaultdict


@router.route('/', defaults=dict(page=0))
@router.route('/page/<int:page>')
@login_required
@ensure_user_stock
def index(page):
    if page < 0:
        page = 0

    pagination = Paginator(Product.query(Product.hidden == False).order(Product.contenttype), page, 20)
    return render_template('tantalus_products.html', showgroup=True, pagination=pagination)


@router.route('.json')
@login_required
@ensure_user_stock
def indexjson():
    return jsonify(Product.query(Product.hidden == False).fetch())

@router.route('/group.json')
@login_required
@ensure_user_stock
def groupjson():
    return jsonify(Group.query().fetch())

@router.route('/btwtype.json')
@login_required
@ensure_user_stock
def btwtypejson():
    return jsonify(BtwType.query().fetch())


@router.route('/group/<string:group_id>', defaults=dict(page=0))
@router.route('/group/<string:group_id>/page/<int:page>')
@login_required
@ensure_user_stock
def showgroup(group_id, page):
    if page < 0:
        page = 0

    group = get_or_none(group_id, Group)
    if group is None:
        return abort(404)

    pagination = Paginator(
        Product.query(Product.hidden == False and Product.group == group.key).order(Product.contenttype),
        page, 20, group_id=group_id
    )
    return render_template('tantalus_products.html', group=group.name, showgroup=False, pagination=pagination)


@router.route('/group/<string:group_id>.json')
@login_required
@ensure_user_stock
def showgroupjson(group_id):
    group = get_or_none(group_id, Group)
    if group is None:
        return abort(404)
    return jsonify(Product.query(Product.hidden == False and Product.group == group.key).fetch())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addproduct():
    form = request.json

    if request.method == "POST":
        group = Group.query(Group.name == form['group']).fetch(1)
        if len(group) == 0:
            if form.get('group', '') != '':
                group = Group(name=form['group'])
                group.put()
            else:
                return abort(403)
        else:
            group = group[0]

        try:
            name = form.get('name') or form.get('contenttype')
            if len(Product.query(Product.contenttype == name).fetch()):
                raise BadValueError("A product with this name already exists.")

            btw = form.get('btw', 0)
            btwtype = BtwType.query(BtwType.percentage == btw).get()
            if btwtype is None:
                btwtype = BtwType(
                    name=str(btw)+"%",
                    percentage=btw
                )
                btwtype.put()

            product = Product(
                contenttype=name,
                tag=form.get('tag', ''),
                group=group.key,
                amount=form.get('amount', 0),
                value=form.get('value', 0),
                hidden=False,
                btwtype=btwtype.key
            ).put()
        except (BadValueError, KeyError) as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html')


@router.route('/edit/<string:product_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editproduct(product_id):
    form = request.json

    product = get_or_none(product_id, Product)
    if product is None:
        return abort(404)

    if request.method == "POST":
        if 'group' in form:
            group = Group.query(Group.name == form.get('group')).fetch(1)
            if len(group) == 0:
                if form.get('group', '') != '':
                    group = Group(name=form['group'])
                    group.put()
                else:
                    return abort(400)
            else:
                group = group[0]
        else:
            group = product.group.get()

        try:
            product.contenttype = form.get('name', form.get('contenttype', product.contenttype))
            product.tag = form.get('tag', '')
            product.group = group.key
            product.amount = form.get('amount', product.amount)
            product.value = form.get('value', product.value)

            btw = form.get('btw', 0)
            btwtype = BtwType.query(BtwType.percentage == btw).get()
            if btwtype is None:
                btwtype = BtwType(
                    name=str(btw) + "%",
                    percentage=btw
                )
                btwtype.put()
            product.btwtype = btwtype.key

            product.put()
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html', product=product)


@router.route('/values.json')
@login_required
@ensure_user_admin
def values():
    vals = defaultdict(int)

    for product in Product.query():
        vals[product.group.get().name] += product.value * product.amount

    return jsonify(dict(vals))
