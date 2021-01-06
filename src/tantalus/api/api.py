from flask_login import login_required
from flask.json import jsonify

from tantalus_db.models import Product, Group, BtwType, Relation, Transaction, User

from tantalus.appfactory.auth import ensure_user_api
from tantalus.api.routers import bp_api as router
from context import get_config


datatypes = {
    'product': Product,
    'group': Group,
    'btwtype': BtwType,
    'relation': Relation,
    'transaction': Transaction,
    'user': User
}

@router.route('/<string:datatype>')
@login_required
@ensure_user_api
def query(datatype):
    if datatype == "yearcode":
        return jsonify({"data": get_config().yearcode})

    if datatype not in datatypes:
        return jsonify({"error": "unknown datatype"}), 404
    
    return jsonify({"data": [e.dict() for e in datatypes[datatype].query.all()]})
