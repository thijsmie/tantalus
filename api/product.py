from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_stock

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Product, Group, TypeGroup
from ndbextensions.paginator import Paginator

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


@router.route('/group/<int:group>', defaults=dict(page=0))
@router.route('/group/<int:group>/page/<int:page>')
@login_required
@ensure_user_stock
def showgroup(group, page):
    if page < 0:
        page = 0

    pagination = Paginator(
        Product.query(Product.hidden == False and Product.group == Key('Group', group,
                                                                       parent=TypeGroup.product_ancestor())).order(
            Product.contenttype),
        page, 20, group=group)
    return render_template('tantalus_products.html', group=Key('Group', group, parent=TypeGroup.product_ancestor()).get().name, showgroup=False,
                           pagination=pagination)


@router.route('/group/<int:group>.json')
@login_required
@ensure_user_stock
def showgroupjson(group):
    return jsonify(Product.query(Product.hidden == False and Product.group == Key('Group', group,
                                                                                  parent=TypeGroup.relation_ancestor())).fetch())


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

            product = Product(
                contenttype=name,
                tag=form.get('tag', ''),
                group=group.key,
                amount=form.get('amount', 0),
                value=form.get('value', 0),
                hidden=False
            ).put()
        except (BadValueError, KeyError) as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html')


@router.route('/edit/<int:product_id>', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def editproduct(product_id):
    form = request.json

    product = Key("Product", product_id, parent=TypeGroup.product_ancestor()).get()

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
        vals[product.group.get().name] += product.value
    
    return jsonify(dict(vals))

