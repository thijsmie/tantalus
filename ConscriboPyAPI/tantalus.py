from google.appengine.ext import ndb

from api import Conscribo
from mapper import TransactionXML, TransactionXMLRow

from ndbextensions.models import ConscriboGroupLink, ConscriboModLink, ConscriboTransactionLink
from ndbextensions.config import Config


@ndb.transactional
def sync_transactions(transactions):
    config = Config.get_config()
    conscribo = Conscribo(config.conscribo_api_url, config.conscribo_api_key, config.conscribo_api_secret)


def transaction_to_transactionXML(transaction, conscribo_link):
    """"Convert a Tantalus Transaction to a Conscribo XML Transaction"""
    txml = TransactionXML(conscribo_link.conscribo_reference,
                          reference="{} {}".format(transaction.relation.get().name, transaction.reference),
                          description=transaction.description)
    txml.date = conscribo_link.bookdate or transaction.deliverydate

    txml.rows.append(TransactionXMLRow(account=conscribo_link.totalaccount, amount=abs(transaction.total),
                                       credit=transaction.total < 0))

    for row in transaction.two_to_one:  # buy
        txml.rows.append(TransactionXMLRow(account=conscribo_link.totalaccount, amount=abs(transaction.total),
                                           credit=transaction.total < 0))