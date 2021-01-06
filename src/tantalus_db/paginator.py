
class Paginator:
    def __init__(self, query, page=0, per_page=20, **kwargs):
        if page < 0:
           page = 0

        self.items = query.limit(per_page).offset(per_page * page).all()
        self.count = query.order_by(None).count()
        self.has_next = page * per_page < self.count
        self.has_prev = page > 0
        self.page = page
        self.page_max = int(self.count / per_page)
        self.extra = kwargs
