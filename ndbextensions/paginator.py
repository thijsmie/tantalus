from flask import abort


class Paginator:
    def __init__(self, query, page=0, per_page=20, **kwargs):
        self.items, cursor, self.has_next = query.fetch_page(per_page, offset=per_page * page)

        if cursor is None and page != 0:
            abort(404)

        self.has_prev = page > 0
        self.page = page
        self.page_max = int(float(query.count()) / per_page + 0.5)
        self.extra = kwargs
