from .base import db
from functools import wraps


def get_or_none(id, obj):
    if type(id) != int:
        try:
            id = int(id)
        except ValueError:
            return None
    return obj.query.filter(obj.id == id).first()


def transactional(func):
    
    @wraps(func)
    def transaction(*args, **kwargs):
        # Nested transactionals become part of the bigger transactional
        if transaction.in_transaction:
            return func(*args, **kwargs)
            
        with db.session.no_autoflush:
            transaction.in_transaction = True
            try:
                ret = func(*args, **kwargs)
                db.session.commit()
                return ret
            except Exception as e:
                db.session.rollback()
                raise e
            finally:
                transaction.in_transaction = False
    
    transaction.in_transaction = False
    return transaction