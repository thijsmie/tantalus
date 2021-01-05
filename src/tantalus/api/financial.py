from flask import render_template
from flask_login import login_required

from tantalus.appfactory.auth import ensure_user_admin
from tantalus.api.actions.group import group_values, group_excl_values
from tantalus.api.actions.service import service_values, service_excl_values
from tantalus.api.routers import bp_financial as router



@router.route('/')
@login_required
@ensure_user_admin
def index():
    return render_template(
        "tantalus_financial_overview.html", 
        group_values=group_values(),
        group_excl_values=group_excl_values(),
        service_values=service_values(),
        service_excl_values=service_excl_values()
    )
