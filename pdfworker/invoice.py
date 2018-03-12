from jinja2 import Template
import markdown
from xhtml2pdf import pisa
from StringIO import StringIO
import os

mydir = os.path.abspath(os.path.dirname(__file__))


def invoice_totaller(transaction):
    sell = transaction["sell"]
    selltotal = 0
    for row in sell:
        selltotal += row["value"]

    buy = transaction["buy"]
    buytotal = 0
    for row in buy:
        buytotal += row["prevalue"]

    service = transaction["service"]
    servicetotal = 0
    for row in service:
        servicetotal += row["value"]

    return {
        "selltotal": selltotal,
        "buytotal": buytotal,
        "servicetotal": servicetotal
    }


with open(os.path.join(mydir, "layout.html")) as f:
    template = f.read()

with open(os.path.join(mydir, "invoice.md")) as f2:
    tx = Template(f2.read())


def make_invoice(transaction, budget=None):
    mx = tx.render(transaction=transaction, budget=budget, totals=invoice_totaller(transaction))
    html = markdown.markdown(mx, ['markdown.extensions.extra'], output_format="html4")
    html = template.replace("{{ html }}", html)
    output = StringIO()
    status = pisa.CreatePDF(html, dest=output)
    return output
