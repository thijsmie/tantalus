from datetime import datetime, date, time
from google.appengine.ext import ndb
from flask.json import jsonify as fjsonify
from api.actions.rows import without_mod_values


def recurse_encode(o):
    if isinstance(o, ndb.Model):
        a = recurse_encode(o.to_dict())
        a['id'] = o.key.id()
        return a
    elif isinstance(o, dict):
        return {k: recurse_encode(v) for k, v in o.iteritems()}
    elif isinstance(o, list):
        return [recurse_encode(v) for v in o]
    elif isinstance(o, ndb.Key):
        return o.id()
    elif isinstance(o, (datetime, date, time)):
        return str(o)
    else:
        return o


tofilter = ["group", "hidden", "value", "description", "amount", "budget", "email"]


def recurse_encode_filtered(o):
    if isinstance(o, ndb.Model):
        a = recurse_encode_filtered(o.to_dict())
        a['id'] = o.key.id()
        return a
    elif isinstance(o, dict):
        ret = {}
        for k, v in o.iteritems():
            if k in tofilter:
                continue
            ret[k] = recurse_encode_filtered(v)
        return ret
    elif isinstance(o, list):
        return [recurse_encode_filtered(v) for v in o]
    elif isinstance(o, ndb.Key):
        return o.id()
    elif isinstance(o, (datetime, date, time)):
        return str(o)
    else:
        return o


def jsonify(object, status_code=200):
    resp = fjsonify(recurse_encode(object))
    resp.status_code = status_code
    return resp


def transaction_recode(o):
    t = recurse_encode(o)

    for row in t['one_to_two']:
        row['contenttype'] = ndb.Key("Product", row['product']).get().contenttype
        row['id'] = row['product']
        del row['value']
        del row['product']
        del row['modamounts']

    for i, row in enumerate(t['two_to_one']):
        row['contenttype'] = ndb.Key("Product", row['product']).get().contenttype
        row['id'] = row['product']
        row['price'] = without_mod_values(o.two_to_one[i])
        del row['value']
        del row['product']
        del row['modamounts']

    for row in t['services']:
        row['contenttype'] = row['service']
        row['price'] = row['value']
        del row['value']
        del row['service']

    return t
