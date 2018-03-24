from google.appengine.ext import ndb
from flask.json import jsonify


def unlink(urlkey, mtype):
    inst = get_or_none(urlkey, mtype)
    if inst is not None:
        inst.key().delete()
        return jsonify({})
    return jsonify({}, 402)
    

def get_or_none(urlkey, mtype):
    key = ndb.Key(urlsafe=urlkey)
    inst = key.get()
    if inst is not None and type(inst) == mtype:
        return inst
    return None
