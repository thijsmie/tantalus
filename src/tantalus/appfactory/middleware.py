"""Flask middleware definitions. This is also where template filters are defined.

To be imported by the application.current_app() factory.
"""

from logging import getLogger

from flask import current_app, render_template, request, session, abort
from markupsafe import Markup

from tantalus_db import encode
from tantalus_db.models import User
import json
from tantalus.appfactory.auth import generate_csrf_token, new_user

LOG = getLogger(__name__)


# Setup default error templates.
@current_app.errorhandler(400)
@current_app.errorhandler(403)
@current_app.errorhandler(404)
@current_app.errorhandler(500)
def error_handler(e):
    code = getattr(e, 'code', 500)  # If 500, e == the exception.
    if code == 500:
        pass
        # Send email to all ADMINS. Disabled, no email conf yet
        # exception_name = e.__class__.__name__
        # view_module = request.endpoint
        # send_exception('{} exception in {}'.format(exception_name, view_module))
    return render_template('{}.html'.format(code)), code


# Template filters.
@current_app.template_filter()
def whitelist(value):
    """Whitelist specific HTML tags and strings.

    Positional arguments:
    value -- the string to perform the operation on.

    Returns:
    Markup() instance, indicating the string is safe.
    """
    translations = {
        '&amp;quot;': '&quot;',
        '&amp;#39;': '&#39;',
        '&amp;lsquo;': '&lsquo;',
        '&amp;nbsp;': '&nbsp;',
        '&lt;br&gt;': '<br>',
    }
    escaped = str(Markup.escape(value))  # Escapes everything.
    for k, v in translations.items():
        escaped = escaped.replace(k, v)  # Un-escape specific elements using str.replace.
    return Markup(escaped)  # Return as 'safe'.


@current_app.template_filter()
def sum_key(value, key):
    """Sums up the numbers in a 'column' in a list of dictionaries or objects.

    Positional arguments:
    value -- list of dictionaries or objects to iterate through.

    Returns:
    Sum of the values.
    """
    values = [r.get(key, 0) if hasattr(r, 'get') else getattr(r, key, 0) for r in value]
    return sum(values)


@current_app.template_filter()
def max_key(value, key):
    """Returns the maximum value in a 'column' in a list of dictionaries or objects.

    Positional arguments:
    value -- list of dictionaries or objects to iterate through.

    Returns:
    Sum of the values.
    """
    values = [r.get(key, 0) if hasattr(r, 'get') else getattr(r, key, 0) for r in value]
    return max(values)


@current_app.template_filter()
def average_key(value, key):
    """Returns the average value in a 'column' in a list of dictionaries or objects.

    Positional arguments:
    value -- list of dictionaries or objects to iterate through.

    Returns:
    Sum of the values.
    """
    values = [r.get(key, 0) if hasattr(r, 'get') else getattr(r, key, 0) for r in value]
    return float(sum(values)) / (len(values) or float('nan'))


@current_app.template_filter()
def format_date(value, date_format='%Y-%m-%d'):
    try:
        return value.strftime(date_format)
    except ValueError:
        return value


@current_app.template_filter()
def format_datetime(value, datetime_format='%Y-%m-%d %H:%M'):
    try:
        return value.strftime(datetime_format)
    except ValueError:
        return value


@current_app.template_filter()
def format_currency(value):
    return "{:.2f}".format(value / 100.0).replace('.', ',')


@current_app.template_filter()
def todict(o):
    return encode.recurse_encode(o)


@current_app.template_filter()
def tr_todict(o):
    return encode.transaction_recode(o)


@current_app.template_filter()
def fancy_json(dct):
    return json.dumps(dct, indent=4)


@current_app.after_request
def apply_transport_security(response):
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


# Setup CSRF-protection
# Please note that JSON is exempt from this, only relevant for call via form that redirect
@current_app.before_request
def csrf_protect():
    if request.method == "POST":
        if request.form and not request.json:
            token = session.get('_csrf_token', None)
            if not token or token != request.form.get('_csrf_token'):
                abort(403)


# On first request check if any users exist. If not, make sure there is a default admin user
@current_app.before_first_request
def ensure_there_is_a_user():
    if len(User.query.all()) == 0:
        from tantalus_db.base import db
        user = new_user("admin", "AdminAdmin", True, None, True, True, True)
        db.session.add(user)
        db.session.commit()
current_app.jinja_env.globals['csrf_token'] = generate_csrf_token
