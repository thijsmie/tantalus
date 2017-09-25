from google.appengine.ext import ndb
from api.actions.transaction import transaction_record
from pdfworker.invoice import make_invoice
from pdfworker.sender import send_invoice
from ndbextensions.models import Transaction, TypeGroup
import webapp2


class InvoiceHandler(webapp2.RequestHandler):
    def post(self):
        transaction = ndb.Key("Transaction", int(self.request.get('transaction')),
                              parent=TypeGroup.transaction_ancestor()).get()
        relation = transaction.relation.get()
        record = transaction_record(transaction)

        def get_budget():
            after = Transaction.query(
                Transaction.reference > transaction.reference, Transaction.relation == transaction.relation).fetch()
            return relation.budget + sum([t.total for t in after])

        if relation.has_budget:
            budget = get_budget()
        else:
            budget = None

        if relation.send_mail:
            pdf = make_invoice(record, budget)
            send_invoice(relation, transaction, pdf)


app = webapp2.WSGIApplication([
    ('/invoice', InvoiceHandler)
], debug=True)
