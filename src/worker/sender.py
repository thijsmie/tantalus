import os
from smtplib import SMTP
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

from config import config


mydir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(mydir, "resources/email.txt")) as f:
    email = f.read()


def send_invoice(relation, transaction, pdf_stringio):
    context = ssl.create_default_context()

    with SMTP(host=config.smtp_host, port=config.smtp_port) as smtp:
        smtp.starttls(context=context)
        smtp.login(config.smtp_user, config.smtp_pass)

        msg = MIMEMultipart()
        
        msg['Subject'] = f"Tantalusfactuur {relation.name}_{transaction.informal_reference:03}"
        msg['From'] = config.smtp_sender
        msg['To'] = relation.email
        
        msg.attach(MIMEText(email.format(
            receiver=relation.name, 
            reference=f"{config.yearcode}-{transaction.reference:04}",
            informal_reference=f"{relation.name}-{transaction.informal_reference:03}")
        , 'plain'))

        attachment = MIMEApplication(pdf_stringio.getvalue(), _subtype='pdf')
        attachment.add_header('Content-Disposition', 'attachment', filename=f"factuur_{relation.name}_{transaction.informal_reference:03}")
        msg.attach(attachment)

        smtp.send_message(msg)
