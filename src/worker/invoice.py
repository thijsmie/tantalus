from flask_weasyprint import HTML
from flask import render_template
from io import BytesIO
import os


def make_invoice(transaction, record, relation, yearcode, budget=None):
    output = BytesIO()
    html = render_template('invoice.html', transaction=transaction, record=record, relation=relation, yearcode=yearcode, budget=budget)
    HTML(string=html).write_pdf(output)
    return output
