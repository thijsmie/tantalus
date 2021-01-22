from flask import request
from flask.json import jsonify
from flask_login import login_required

from tantalus.appfactory.auth import ensure_user_pos
from tantalus.api.routers import bp_pos_client as router

from tantalus.api.actions.pos import new_pos_sale
from tantalus.appfactory.auth import do_login, do_logout, current_user

from tantalus_db.models import PosEndpoint, PosProduct


@router.route('/login', methods=["POST"])
def pos_login():
    data = request.json
    if not 'username' in data or not 'password' in data:
        return jsonify(error="Supply username and password"), 400
    if not do_login(data['username'], data['password'], True):
        return jsonify(error="Invalid login"), 403
    if not current_user.user.right_posaction:
        do_logout()
        return jsonify(error="Invalid login"), 403
    return jsonify(message="logged in")


@router.route('/logout', methods=["POST"])
@login_required
@ensure_user_pos
def pos_logout():
    do_logout()
    return jsonify(message="logged out")


@router.route('/products')
@login_required
@ensure_user_pos
def pos_products():
    return jsonify(products=[p.dict() for p in PosProduct.query.filter(PosProduct.discontinued == False).all()])


@router.route('/endpoints')
@login_required
@ensure_user_pos
def pos_endpoints():
    return jsonify(endpoints=[e.dict() for e in PosEndpoint.query.all()])


@router.route('/sell', methods=["POST"])
@login_required
@ensure_user_pos
def pos_sale():
    data = request.json
    if not all(a in data for a in ['product', 'endpoint', 'amount']):
        return jsonify(error="Supply product, endpoint and amount"), 400
    try:
        sale = new_pos_sale(data)
    except:
        return jsonify(error="Server error"), 400
    return jsonify(sale=sale.dict())