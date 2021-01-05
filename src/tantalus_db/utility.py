from .base import db


def get_or_none(id, obj):
    if type(id) != int:
        try:
            id = int(id)
        except ValueError:
            return None
    return obj.query.filter(obj.id == id).first()


def transactional(func):
    def new_func(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
            db.session.commit()
            return ret
        except Exception as e:
            db.session.rollback()
            raise e

    return new_func