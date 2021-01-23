from datetime import datetime, date, time
from inspect import isfunction

from sqlalchemy.orm import class_mapper, relationship
from flask.json import jsonify as flask_jsonify

from .base import Base
from .models import Product, BtwType
from .utility import get_or_none



def recurse_encode(o):
    if isinstance(o, Base):
        return {k: recurse_encode(v) for k,v in o.dict().items()}
    elif isinstance(o, dict):
        return {k: recurse_encode(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [recurse_encode(v) for v in o]
    elif isinstance(o, (datetime, date, time)):
        return str(o)
    elif isfunction(o):
        return "[func]"
    else:
        return o


def transaction_recode(o):
    t = recurse_encode(o)

    for row in t['one_to_two']:
        row['contenttype'] = get_or_none(row["product"], Product).contenttype
        row['id'] = row['product']
        del row['value']
        del row['product']

    for i, row in enumerate(t['two_to_one']):
        row['contenttype'] = get_or_none(row["product"], Product).contenttype
        row['id'] = row['product']
        row['price'] = row['prevalue']
        del row['value']
        del row['product']

    for row in t['services']:
        row['contenttype'] = row['service']
        row['price'] = row['value']
        row['btw'] = get_or_none(row['btwtype'], BtwType).percentage
        del row['value']
        del row['service']
        del row['btwtype']

    return t


def jsonify(arg, status_code=200, **kwargs):
    dict = recurse_encode(arg)
    dict.update(**kwargs)
    return flask_jsonify(dict), status_code