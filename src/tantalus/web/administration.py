import re

from flask import render_template, request, redirect, url_for
from flask_login import login_required

from tantalus_db.base import db
from tantalus_db.config import Setting
from tantalus_db.models import PosSale

from tantalus.appfactory.auth import ensure_user_admin
from tantalus.web.routers import bp_administration as router
from tantalus.appfactory import flash

from worker.worker import advance_bookyear


@router.route('/')
@login_required
@ensure_user_admin
def index():
    unprocessed = PosSale.query.filter(PosSale.processed == False).count()
    return render_template('tantalus_administration.html', settings=Setting.query.order_by(Setting.name).all(), unprocessed=unprocessed)



@router.route('/setting/<int:id>', methods=["POST"])
@login_required
@ensure_user_admin
def setting(id):
    form = request.form or request.json
    setting = Setting.query.get_or_404(id)
    if not form or not 'value' in form:
        flash.danger('No value was posted')
        return redirect(url_for('.index'))

    setting.value = form['value']
    db.session.commit()
    flash.info('The setting was updated')
    return redirect(url_for('.index'))


@router.route('/advance', methods=['POST'])
@login_required
@ensure_user_admin
def advance():
    form = request.form or request.json
    if not form or not 'yearcode' in form or not re.match(r'\d{4}', form['yearcode']):
        flash.danger('No proper yearcode was posted')
        return redirect(url_for('.index'))
    advance_bookyear(form['yearcode'])
    flash.warning("Advance bookyear has been scheduled. Time to close this tab (and all other tantalus tabs) and wait for it to complete.")
    return redirect(url_for('tantalus.index'))
    
