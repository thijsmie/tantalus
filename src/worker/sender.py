import os
from smtplib import SMTP_SSL, SMTP
from email.message import EmailMessage
from email.mime.application import MIMEApplication

from context import get_config


mydir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(mydir, "resources/email.txt")) as f:
    email = f.read()


def send_invoice(relation, transaction, pdf_stringio):
    config = get_config()

    if config.smtp:
        smtp_host = config.smtp.get('host', 'localhost')
        smtp_port = config.smtp.get('port', 465)
        smtp_inst = SMTP_SSL if config.smtp.get('secure', True) else SMTP
        smtp_sender = config.smtp.get('sender', 'test@example.com')
    else:
        return

    with smtp_inst(host=smtp_host, port=smtp_port) as smtp:
        msg = EmailMessage()
        msg.set_content(email.format(
            receiver=relation.name, 
            reference=f"{config.yearcode}-{transaction.reference:04}",
            informal_reference=f"{relation.name}-{transaction.informal_reference:03}")
        )

        msg['Subject'] = f"Tantalusfactuur {relation.name}_{transaction.informal_reference:03}"
        msg['From'] = smtp_sender
        msg['To'] = relation.email

        attachment = MIMEApplication(pdf_stringio.getvalue(), _subtype='pdf')
        attachment.add_header('Content-Disposition', 'attachment', filename=f"factuur_{relation.name}_{transaction.informal_reference:03}")
        msg.attach(attachment)

        smtp.send_message(msg)
