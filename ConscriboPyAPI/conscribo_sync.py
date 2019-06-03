from collections import defaultdict
from google.appengine.ext import ndb

from conscribo_api import Conscribo
from conscribo_mapper import TransactionXML, TransactionXMLRow, ResultException

from ndbextensions.models import TypeGroup
from ndbextensions.conscribo import ConscriboConfig, ConscriboTransactionLink
from ndbextensions.config import Config

from api.actions.transaction import transaction_record
import traceback


@ndb.transactional(xg=True)
def sync_transactions(transactions):
    config = Config.get_config()
    conscribo = Conscribo(config.conscribo_api_url, config.conscribo_api_key, config.conscribo_api_secret)

    for t in transactions:
        link = ConscriboTransactionLink.query(ConscriboTransactionLink.transaction == t.key,
                                              ancestor=TypeGroup.conscribo_ancestor()).get()
        if link is None:
            continue
        xml = transaction_to_transactionXML(t, link)

        try:
            conscribo.add_change_transaction(xml)

            link.pushed_revision = t.revision
            link.feedback = "Succeeded"
        except ResultException as e:
            link.feedback = str(e)
        except:
            link.feedback = "Error voor thijs: " + traceback.format_exc()
        link.put()


def transaction_to_transactionXML(transaction, conscribo_link):
    """"Convert a Tantalus Transaction to a Conscribo XML Transaction"""
    txml = TransactionXML(conscribo_link.conscribo_reference,
                          reference="1819-{} {} {}".format(str(transaction.reference), transaction.relation.get().name,
                                                           transaction.informal_reference),
                          description="{} ({} {})".format(transaction.description, transaction.relation.get().name,
                                                          transaction.informal_reference))
    txml.date = conscribo_link.bookdate or transaction.deliverydate

    config = ConscriboConfig.get_config()
    todo_account = config.get("todo", 999)
    rel_link = config.get("relations", {}).get(transaction.relation.get().name)

    if rel_link is None:
        total_account = todo_account
    else:
        total_account = rel_link

    record = transaction_record(transaction)

    for group, btwvalues in rows_groups_btws_totals(record["sell"]).iteritems():
        inventory = config.get("groups", {}).get(group).get("inventory") or todo_account

        for btwt, values in btwvalues.iteritems():
            vatcode = config.get("vatcodes", {})[btwt]  # error if btwtype is not vatcoded: intentional!

            txml.rows.append(
                TransactionXMLRow(account=inventory, amount=values[0], credit=True, vatcode=vatcode, vat=values[1]))
            txml.rows.append(
                TransactionXMLRow(account=total_account, amount=values[0] + values[1], credit=False))
            txml.description += "\nSell Group total {}, btw{} with value {:.2f}.".format(group, btwt, values[2] / 100.0)

    for group, btwvalues in rows_groups_btws_totals(record["buy"], record["two_to_one_has_btw"]).iteritems():
        inventory = config.get("groups", {}).get(group, {}).get("inventory") or todo_account
        profit = config.get("groups", {}).get(group, {}).get("profit") or todo_account

        for btwt, values in btwvalues.iteritems():
            vatcode = config.get("vatcodes", {})[btwt]  # error if btwtype is not vatcoded: intentional!

            txml.rows.append(
                TransactionXMLRow(account=inventory, amount=abs(values[2]), credit=False))
            txml.rows.append(
                TransactionXMLRow(account=profit, amount=abs(values[2] + values[1]), credit=True))
            txml.rows.append(
                TransactionXMLRow(account=profit, amount=abs(values[0] + values[1]), credit=False, vatcode=vatcode,
                              vat=abs(values[1])))
            txml.rows.append(
                TransactionXMLRow(account=total_account, amount=abs(values[0] + values[1]), credit=True))
            txml.description += "\nBuy Group total {}, btw{} with value {:.2f}.".format(group, btwt, values[2] / 100.0)

    for service in record["service"]:
        vatcode = config.get("vatcodes", {})[str(service["btw"])]
        txml.rows.append(TransactionXMLRow(account=total_account, amount=abs(service["value"]),
                                           credit=service["value"] < 0))
        txml.rows.append(
            TransactionXMLRow(account=todo_account, amount=abs(service["value"] - service["btwvalue"]),
                              credit=service["value"] > 0, vatcode=vatcode, vat=service["btwvalue"]))
        txml.description += "\nService {} with value {:.2f}.".format(service["contenttype"], service["value"] / 100.0)

    return txml


def rows_groups_btws_totals(rowset, includes_btw=True):
    group_valuebtw = defaultdict(lambda: defaultdict(lambda: [0., 0., 0.]))

    for row in rowset:
        group_valuebtw[row["group"]][str(row["btw"])][0] += row["prevalue"] - (row["btwvalue"] if includes_btw else 0)
        group_valuebtw[row["group"]][str(row["btw"])][1] += row["btwvalue"]
        group_valuebtw[row["group"]][str(row["btw"])][2] += row.get("value_excl", row["value"])

    for group, values in group_valuebtw.iteritems():
        for btwt, valuebtw in values.iteritems():
            group_valuebtw[group][btwt][0] = int(round(valuebtw[0]))
            group_valuebtw[group][btwt][1] = int(round(valuebtw[1]))

    return group_valuebtw
