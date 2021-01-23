from datetime import datetime
from flask import render_template, request, redirect, url_for
from flask.json import jsonify
from flask_login import login_required

from worker.worker import pos_transaction

from tantalus_db.base import db

from tantalus.appfactory.auth import ensure_user_admin
from tantalus.web.routers import bp_pos as router

import tantalus.appfactory.flash as flash
from tantalus.logic.pos import new_pos_product, new_pos_service, \
    edit_pos_product, edit_pos_service, discontinue_pos_product, \
    add_pos_endpoint

from tantalus_db.models import PosEndpoint, PosProduct, PosSale, Product, Relation
from tantalus_db.paginator import Paginator


@router.route('/')
@login_required
@ensure_user_admin
def index():
    return render_template(
        'tantalus_posproducts.html',
        posproducts=PosProduct.query.filter(
            PosProduct.discontinued == False).all(),
        posendpoints=PosEndpoint.query.all(),
        products=Product.query.filter(Product.discontinued == False).all(),
        relations=Relation.query.all()
    )


@router.route('/view/<int:pos_product_id>')
@login_required
@ensure_user_admin
def view(pos_product_id):
    product = PosProduct.query.get_or_404(pos_product_id)
    return render_template(
        'tantalus_posproduct.html',
        product=product,
        products=Product.query.filter(Product.discontinued == False).all()
    )


@router.route('/add/product', methods=["POST"])
@login_required
@ensure_user_admin
def add_product():
    form = request.json

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    if not all(field in form for field in ["name", "product"]):
        return jsonify({"messages": ["Missing required fields"]}), 400

    try:
        product = new_pos_product(form)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(product.dict())


@router.route('/edit/product/<int:pos_product_id>', methods=["POST"])
@login_required
@ensure_user_admin
def edit_product(pos_product_id):
    form = request.json
    posproduct = PosProduct.query.get_or_404(pos_product_id)

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    try:
        edit_pos_product(posproduct, form)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(posproduct.dict())


@router.route('/add/service', methods=["POST"])
@login_required
@ensure_user_admin
def add_service():
    form = request.json

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    if not all(field in form for field in ["name", "service", "price", "btw"]):
        return jsonify({"messages": ["Missing required fields"]}), 400

    try:
        service = new_pos_service(form)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(service.dict())


@router.route('/edit/service/<int:pos_product_id>', methods=["POST"])
@login_required
@ensure_user_admin
def edit_service(pos_product_id):
    form = request.json
    posproduct = PosProduct.query.get_or_404(pos_product_id)

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    try:
        edit_pos_service(posproduct, form)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(posproduct.dict())


@router.route('/discontinue/<int:pos_product_id>', methods=["POST"])
@login_required
@ensure_user_admin
def discontinue(pos_product_id):
    form = request.json
    posproduct = PosProduct.query.get_or_404(pos_product_id)

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    try:
        discontinue_pos_product(posproduct)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(posproduct.dict())


@router.route('/add/endpoint', methods=["POST"])
@login_required
@ensure_user_admin
def add_endpoint():
    form = request.json

    if not form:
        return jsonify({"messages": ["No json posted"]}), 400

    try:
        endpoint = add_pos_endpoint(form)
    except:
        return jsonify({"messages": ["Invalid data"]}), 400

    return jsonify(endpoint.dict())


@router.route('/endpoint/<int:endpoint_id>', defaults=dict(page=0))
@router.route('/endpoint/<int:endpoint_id>/page/<int:page>')
@login_required
@ensure_user_admin
def endpoint(endpoint_id, page):
    endpoint = PosEndpoint.query.get_or_404(endpoint_id)
    sales_paginator = Paginator(PosSale.query.filter(PosSale.posendpoint == endpoint).order_by(
        PosSale.time_created.desc()), page=page, per_page=40, endpoint_id=endpoint_id)
    return render_template(
        'tantalus_posendpoint.html',
        endpoint=endpoint,
        sales_paginator=sales_paginator
    )


@router.route('/endpoint/<int:endpoint_id>/process', methods=["POST"])
@login_required
@ensure_user_admin
def endpoint_gen(endpoint_id):
    endpoint = PosEndpoint.query.get_or_404(endpoint_id)
    form = request.form or request.json

    try:
        date_start = datetime.strptime(form["start"], "%Y-%m-%d").date()
        date_end = datetime.strptime(form["end"], "%Y-%m-%d").date()

        pos_transaction(
            endpoint.id, 
            date_start.strftime("%Y-%m-%d"),
            date_end.strftime("%Y-%m-%d")
        )
    except:
        flash.danger("Invalid data entered")
        return redirect(url_for('.endpoint', endpoint_id=endpoint_id, page=0)), 400
    flash.success("Data submitted. It might take a few seconds for the transaction to process.")
    return redirect(url_for('.endpoint', endpoint_id=endpoint_id, page=0))
        
    
