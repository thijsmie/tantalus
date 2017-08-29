from flask import render_template, redirect, url_for, request, jsonify, current_app
from flask_login import current_user
from tantalus import bp_base as router

from google.appengine.ext.db import stats

from appfactory import flash
from appfactory.auth import do_login, do_logout


@router.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template("home.html")
    else:
        gstats = stats.GlobalStat.all().get()
        return render_template("base_index.html", stats=gstats)


@router.route('/login', methods=["GET", "POST"])
def login():
    form = request.form
    if 'username' in form:
        if do_login(form['username'], form['password'], 'remember-me' in form):
            flash.success("Logged in successfully.")
        else:
            flash.danger("Incorrect login data, please try again.")
    return redirect(url_for('.index'))


@router.route('/logout')
def logout():
    do_logout()
    return redirect(url_for('.index'))


@router.route('/token.json')
def token():
    return jsonify(_csrf_token=current_app.jinja_env.globals['csrf_token']())
