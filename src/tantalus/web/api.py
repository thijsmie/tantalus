from flask_login import login_required
from flask.json import jsonify

from tantalus_db.models import PosEndpoint, PosProduct, PosSale, Product, Group, BtwType, Relation, Transaction, User

from tantalus.appfactory.auth import ensure_user_api
from tantalus.web.routers import bp_api as router
from config import config

import re

filter_re = re.compile("(\w*)(=|<|>)(.*)")

datatypes = {
    'product': Product,
    'group': Group,
    'btwtype': BtwType,
    'relation': Relation,
    'transaction': Transaction,
    'user': User,
    'posendpoint': PosEndpoint,
    'posproduct': PosProduct,
    'possale': PosSale
}

@router.route('/<string:datatype>', defaults={"filters": ""})
@router.route('/<string:datatype>/<string:filters>')
@login_required
@ensure_user_api
def query(datatype, filters):
    if datatype == "yearcode":
        return jsonify({"data": config.yearcode})

    if datatype not in datatypes:
        return jsonify({"error": "unknown datatype"}), 404

    cls = datatypes[datatype]
    query = cls.query

    if filters != "":
        for filter in filters.split(','):
            m = filter_re.match(filter)
            if not m:
                return jsonify({"error": "incorrect filter"}), 400
            field, op, value = m.groups()
            if field not in cls.filters():
                return jsonify({"error": "unknown filter"}), 400
            if op == '=':
                query = query.filter(cls.filters()[field] == value)
            elif op == '>':
                query = query.filter(cls.filters()[field] > value)
            elif op == '<':
                query = query.filter(cls.filters()[field] < value)
    
    return jsonify({"data": [e.dict() for e in query.all()]})
