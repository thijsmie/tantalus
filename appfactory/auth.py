from flask_login import LoginManager, login_user, logout_user, current_user
from flask import redirect, abort
from functools import wraps
from passlib.hash import pbkdf2_sha256 as hashf

from google.appengine.ext import ndb
from google.appengine.api import memcache

from appfactory import flash
from ndbextensions.models import User

# Random session key generation, inspired by django.utils.crypto.get_random_string
import random

try:
    random = random.SystemRandom()
except NotImplementedError:
    from flask import current_app

    current_app.logger.log.critical("Insecure random! Please make random.SystemRandom available!")


def generate_random_string(length):
    return ''.join(
        [random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.,') for _ in range(length)])


auth = LoginManager()
auth.login_view = "tantalus.login"
auth.session_protection = "strong"


@auth.user_loader
def load_user(session_token):
    user = memcache.get(session_token)
    if user is not None:
        return user
    user = User.query(User.session == session_token).get()
    memcache.add(key=session_token, value=user, time=60)
    return user


def do_login(username, password, rememberme):
    user = User.query(User.username == username).get()

    if user is None:
        return False

    if not hashf.verify(password, user.passhash):
        return False

    user.session = generate_random_string(64)
    user.put()

    memcache.add(key=user.session, value=user, time=60)

    return login_user(user, remember=rememberme)


def do_logout():
    logout_user()


def update_password(user, password):
    user.passhash = hashf.hash(password)


def new_user(username, password, isadmin=False, relation=None, viewstock=False, viewtransactions=False, ispos=False):
    user = User(
        username=username,
        passhash=hashf.hash(password),
        right_admin=isadmin,
        right_viewstock=viewstock,
        right_viewalltransactions=viewtransactions,
        right_posaction=ispos
    )

    if relation is not None:
        user.relation = ndb.Key("Relation", relation)
        if user.relation.get() is None:
            abort(400)

    return user


def ensure_user_admin(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin:
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_pos(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin:
            if not current_user.right_pos:
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_relation(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin or current_user.right_viewalltransactions:
            if not (current_user.relation is not None and current_user.relation == kwargs.get('relation_id')):
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_transactions(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin or current_user.right_viewalltransactions:
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_transaction(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin or current_user.right_viewalltransactions:
            transaction = ndb.Key("Transaction", kwargs.get('transaction_id')).get()
            if transaction is None or not (
                            current_user.relation is not None and current_user.relation == transaction.relation):
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_stock(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.right_admin:
            if not current_user.right_viewstock:
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function
