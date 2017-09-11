from flask import render_template, redirect, url_for, request
from flask_login import current_user
from tantalus import bp_base as router

from google.appengine.ext.db import stats

from appfactory import flash
from appfactory.auth import do_login, do_logout
from ndbextensions.ndbjson import jsonify


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


@router.route('/login.json', methods=["POST"])
def token():
    form = request.json
    try:
        if do_login(form['username'], form['password'], 'remember-me' in form):
            return jsonify({})
        else:
            return jsonify({"error": "Incorrect login!"}, 401)
    except KeyError:
        return jsonify({"error": "Supply username and password!"}, 400)
