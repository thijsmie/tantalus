from flask import render_template, redirect, url_for, request
from flask_login import current_user

from tantalus.api.routers import bp_base as router
from tantalus.appfactory import flash
from tantalus.appfactory.auth import do_login, do_logout

from tantalus_db.base import db
from tantalus_db.encode import jsonify


@router.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template("home.html")
    else:
        return render_template("base_index.html")


@router.route('/login', methods=["GET", "POST"])
def login():
    form = request.form
    if 'username' in form:
        if do_login(form['username'], form['password'], 'remember-me' in form):
            db.session.commit()
            flash.success("Logged in successfully.")
        else:
            flash.danger("Incorrect login data, please try again.")
    return redirect(url_for('.index'))


@router.route('/logout')
def logout():
    do_logout()
    db.session.commit()
    return redirect(url_for('.index'))


@router.route('/login.json', methods=["POST"])
def token():
    form = request.json
    try:
        if do_login(form['username'], form['password'], 'remember-me' in form):
            db.session.commit()
            return jsonify({})
        else:
            return jsonify({"error": "Incorrect login!"}, 401)
    except KeyError:
        return jsonify({"error": "Supply username and password!"}, 400)
