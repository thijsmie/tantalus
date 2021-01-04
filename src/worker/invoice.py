from jinja2 import Template
import markdown
from xhtml2pdf import pisa
from StringIO import StringIO
import os

mydir = os.path.abspath(os.path.dirname(__file__))


with open(os.path.join(mydir, "resources/layout.html")) as f:
    template = f.read()

with open(os.path.join(mydir, "resources/invoice.md")) as f2:
    tx = Template(f2.read())


def make_invoice(transaction, relation, yearcode, budget=None):
    mx = tx.render(transaction=transaction, relation=relation, budget=budget, yearcode=yearcode)
    html = markdown.markdown(mx, ['markdown.extensions.extra'], output_format="html4")
    html = template.replace("{{ html }}", html)
    output = StringIO()
    status = pisa.CreatePDF(html, dest=output)
    return output
