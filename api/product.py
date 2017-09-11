from google.appengine.ext.ndb import Key
from google.appengine.ext.db import BadValueError

from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_stock

from ndbextensions.ndbjson import jsonify
from ndbextensions.models import Product, Mod, Group, TypeGroup
from ndbextensions.paginator import Paginator

from tantalus import bp_product as router


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

            losemods = [Key("Mod", id, parent=TypeGroup.product_ancestor()) for id in (form.get('losemods') or [])]
            for mod in losemods:
                if mod.get() is None:
                    raise BadValueError("Mod {} does not exists.".format(mod))

            gainmods = [Key("Mod", id, parent=TypeGroup.product_ancestor()) for id in (form.get('gainmods') or [])]
            for mod in gainmods:
                if mod.get() is None:
                    raise BadValueError("Mod {} does not exists.".format(mod))

            product = Product(
                contenttype=name,
                tag=form.get('tag', ''),
                group=group.key,
                amount=form.get('amount', 0),
                value=form.get('value', 0),
                hidden=False,
                losemods=losemods,
                gainmods=gainmods
            ).put()
        except (BadValueError, KeyError) as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html', mods=Mod.query().fetch())


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
            losemods = product.losemods
            if 'losemods' in form:
                losemods = [Key("Mod", id, parent=TypeGroup.product_ancestor()) for id in form.get('losemods')]
            for mod in losemods:
                if mod.get() is None:
                    raise BadValueError("Mod {} does not exists.".format(mod))

            gainmods = product.gainmods
            if 'gainmods' in form:
                gainmods = [Key("Mod", id, parent=TypeGroup.product_ancestor()) for id in form.get('gainmods')]
            for mod in gainmods:
                if mod.get() is None:
                    raise BadValueError("Mod {} does not exists.".format(mod))

            product.contenttype = form.get('name', form.get('contenttype', product.contenttype))
            product.tag = form.get('tag', '')
            product.group = group.key
            product.amount = form.get('amount', product.amount)
            product.value = form.get('value', product.value)
            product.losemods = losemods
            product.gainmods = gainmods
            product.put()
        except BadValueError as e:
            return jsonify({"messages": [e.message]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html', product=product, mods=Mod.query().fetch())
