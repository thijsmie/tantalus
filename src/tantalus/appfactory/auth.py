from flask_login import LoginManager, login_user, logout_user, current_user
from flask import redirect, abort, session
from functools import wraps
from passlib.hash import pbkdf2_sha256 as hashf

from tantalus.appfactory import flash

from tantalus_db.base import db
from tantalus_db.models import Session, User, Relation, Transaction
from tantalus_db.utility import get_or_none

from config import config


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


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_random_string(16)
    return session['_csrf_token']


auth = LoginManager()
auth.login_view = "tantalus.login"
auth.session_protection = "strong"


@auth.user_loader
def load_user(session_token):
    return Session.query.filter(Session.session == session_token).first()


def do_login(username, password, rememberme):
    if config.nologin.lower() == 'true':
        return False

    user = User.query.filter(User.username == username).first()

    if user is None:
        return False

    if not hashf.verify(password, user.passhash):
        return False

    session = Session(
        user=user,
        session=generate_random_string(128)
    )
    db.session.add(session)
    db.session.commit()

    return login_user(session, remember=rememberme)


def do_logout():
    try:
        current_user.delete()
    except:
        pass
    logout_user()


def update_password(user, password):
    user.passhash = hashf.hash(password)


def new_user(username, password, isadmin=False, relation=None, viewstock=False, viewtransactions=False, ispos=False, api=False):
    user = User(
        username=username,
        passhash=hashf.hash(password),
        right_admin=isadmin,
        right_viewstock=viewstock,
        right_viewalltransactions=viewtransactions,
        right_posaction=ispos,
        right_api=api
    )

    if relation is not None:
        rel = get_or_none(relation, Relation)
        if rel is None:
            abort(400)
        user.relation = rel

    return user


def ensure_user_admin(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.user.right_admin:
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_pos(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.user.right_admin or current_user.user.right_posaction):
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_relation(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.user.right_admin or current_user.user.right_viewalltransactions):
            if not (current_user.user.relation is not None and current_user.user.relation == kwargs.get('relation_id')):
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_transactions(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.user.right_admin or current_user.user.right_viewalltransactions):
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_transaction(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.user.right_admin or current_user.user.right_viewalltransactions):
            transaction = get_or_none(kwargs.get('transaction_id'), Transaction)
            if transaction is None or not (current_user.user.relation is not None \
                    and current_user.user.relation == transaction.relation):
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_stock(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.user.right_admin:
            if not current_user.user.right_viewstock:
                flash.danger("Your user account is not allowed to perform this action.")
                return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def ensure_user_api(f):
    # Note, should be placed below @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.user.right_api:
            flash.danger("Your user account is not allowed to perform this action.")
            return redirect('/'), 403
        return f(*args, **kwargs)
    return decorated_function
