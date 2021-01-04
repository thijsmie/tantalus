from flask import render_template, request, abort
from flask_login import login_required

from appfactory.auth import ensure_user_admin, ensure_user_stock

from tantalus_db.base import db
from tantalus_db.encode import jsonify
from tantalus_db.models import Product
from tantalus_db.utility import get_or_none

from api.common import common_collection
from api.actions.group import group_values
from api.actions.product import new_product, edit_product

from tantalus.api.routers import bp_product as router


common_collection(
    router,
    ensure_user_stock,
    Product.query.filter(product.hidden == False).order_by(Product.contenttype), 
    'tantalus_products_showgroup.html'
)


@router.route('/group.json')
@login_required
@ensure_user_stock
def groupjson():
    return jsonify(Group.query.all())


@router.route('/btwtype.json')
@login_required
@ensure_user_stock
def btwtypejson():
    return jsonify(BtwType.query.all())


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
        Product.query.filter(Product.hidden == False and Product.group == group.key).order_by(Product.contenttype),
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
    return jsonify(Product.query.filter(Product.hidden == False and Product.group == group.key).all())


@router.route('/add', methods=["GET", "POST"])
@login_required
@ensure_user_admin
def addproduct():
    form = request.json

    if request.method == "POST":
        try:
            new_product(form)
        except:
            return jsonify({"messages": ["Invalid data"]}, 400)
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
        try:
            edit_product(product, form)
        except:
            return jsonify({"messages": ["Invalid data"]}, 400)
        return jsonify(product)

    return render_template('tantalus_product.html', product=product)


@router.route('/values.json')
@login_required
@ensure_user_admin
def values():
    return jsonify(group_values())
