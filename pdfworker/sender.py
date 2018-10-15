from google.appengine.api import mail


def send_invoice(relation, transaction, pdf_stringio):
    mail.send_mail(sender="invoice@new-tantalus.appspotmail.com",
                   to=relation.email,
                   subject="Tantalusfactuur 1819-{}".format(str(transaction.reference).zfill(4)),
                   attachments=[
                       ("factuur_{}_{}.pdf".format(relation.name, transaction.informal_reference), pdf_stringio.getvalue())],
                   body="""This is an automatically generated email from a no reply address. If you have any questions or notes about this invoice, please mail to demeter.olympus@science.ru.nl or penningmeester.voorraad@science.ru.nl

---

Deze mail is automatisch gegenereerd en verzonden vanaf een noreply-adres. Mochten er vragen of opmerkingen zijn over deze factuur, dan kunnen die gemaild worden naar demeter.olympus@science.ru.nl of penningmeester.voorraad@science.ru.nl""")
