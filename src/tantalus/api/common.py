
from flask_login import login_required
from appfactory.auth import ensure_user_admin

from tantalus_db.encode import jsonify
from tantalus_db.paginator import Paginator



def common_collection(router, protection, query, template)
    @router.route('/', defaults=dict(page=0))
    @router.route('/page/<int:page>')
    @login_required
    @protection
    def index(page):
        if page < 0:
            page = 0

        pagination = Paginator(query, page, 20)
        return render_template('tantalus_relations.html', pagination=pagination)


    @router.route('.json')
    @login_required
    @protection
    def indexjson():
        return jsonify(query.all())