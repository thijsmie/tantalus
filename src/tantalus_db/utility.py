from contextlib import contextmanager
from .base import db


def get_or_none(id, obj):
    if type(id) != int:
        try:
            id = int(id)
        except ValueError:
            return None
    return obj.query.filter(obj.id == id).first()


@contextmanager
def transaction():
    db.session.commit()
    
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e