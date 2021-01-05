from collections import defaultdict

from .conscribo_api import Conscribo
from .conscribo_mapper import TransactionXML, TransactionXMLRow, ResultException

from tantalus_db.conscribo import ConscriboConfig, ConscriboTransactionLink
from tantalus_db.utility import transactional

from context import get_config

from tantalus.api.actions.transaction import transaction_record
import traceback


@transactional
def sync_transactions(transactions):
    config = get_config()
    conscribo = Conscribo(config.conscribo.api_url, config.conscribo.api_key, config.conscribo.api_secret)

    for t in transactions:
        link = t.conscribo_transaction
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


def transaction_to_transactionXML(transaction, conscribo_link):
    """"Convert a Tantalus Transaction to a Conscribo XML Transaction"""
    mconfig = get_config()

    txml = TransactionXML(conscribo_link.conscribo_reference,
                          reference="{}-{} {} {}".format(mconfig.yearcode, str(transaction.reference), transaction.relation.name,
                                                           transaction.informal_reference),
                          description="{} ({} {})".format(transaction.description, transaction.relation.name,
                                                          transaction.informal_reference))
    txml.date = conscribo_link.bookdate or transaction.deliverydate

    config = ConscriboConfig.get_config()
    todo_account = config.get("todo", 999)
    rel_link = config.get("relations", {}).get(transaction.relation.name)

    if rel_link is None:
        total_account = todo_account
    else:
        total_account = rel_link

    record = transaction_record(transaction)
    
    absolute_total = 0

    for group, btwvalues in rows_groups_btws_totals(record["sell"]).items():
        inventory = config.get("groups", {}).get(group).get("inventory") or todo_account

        for btwt, values in btwvalues.iteritems():
            vatcode = config.get("vatcodes", {})[btwt]  # error if btwtype is not vatcoded: intentional!

            txml.rows.append(
                TransactionXMLRow(account=inventory, amount=values[0], credit=True, vatcode=vatcode, vat=values[1]))
            #txml.rows.append(
            #   TransactionXMLRow(account=total_account, amount=values[0] + values[1], credit=False))
            absolute_total += values[0] + values[1]
            txml.description += "\nSell Group total {}, btw{} with value {:.2f}.".format(group, btwt, values[2] / 100.0)

    for group, btwvalues in rows_groups_btws_totals(record["buy"], record["two_to_one_has_btw"]).items():
        inventory = config.get("groups", {}).get(group, {}).get("inventory") or todo_account
        profit = config.get("groups", {}).get(group, {}).get("profit") or todo_account

        for btwt, values in btwvalues.items():
            vatcode = config.get("vatcodes", {})[btwt]  # error if btwtype is not vatcoded: intentional!
            print(values[0], values[1], values[2], values[3])

            if values[1] == 0:
                txml.rows.append(
                    TransactionXMLRow(account=inventory, amount=abs(values[0]), credit=False))
                #txml.rows.append(
                #    TransactionXMLRow(account=total_account, amount=abs(values[0]), credit=True))
                absolute_total -= abs(values[0])
            else:
                txml.rows.append(
                    TransactionXMLRow(account=inventory, amount=abs(values[3]), credit=False))
                #txml.rows.append(
                #    TransactionXMLRow(account=total_account, amount=abs(values[0] + values[1]), credit=True))
                absolute_total -= abs(values[0] + values[1])
                txml.rows.append(
                    TransactionXMLRow(account=profit, amount=abs(values[3]), credit=True))
                txml.rows.append(
                    TransactionXMLRow(account=profit, amount=abs(values[0]), credit=False, vatcode=vatcode,
                                  vat=abs(values[1])))
            txml.description += "\nBuy Group total {}, btw{} with value {:.2f}.".format(group, btwt, values[2] / 100.0)

    for service in record["service"]:
        vatcode = config.get("vatcodes", {})[str(service["btw"])]
        txml.rows.append(TransactionXMLRow(account=total_account, amount=abs(service["value"]),
                                           credit=service["value"] < 0))
        txml.rows.append(
            TransactionXMLRow(account=todo_account, amount=abs(service["value"] - service["btwvalue"]),
                              credit=service["value"] > 0, vatcode=vatcode, vat=service["btwvalue"]))
        txml.description += "\nService {} with value {:.2f}.".format(service["contenttype"], service["value"] / 100.0)
    txml.rows.append(
        TransactionXMLRow(account=total_account, amount=abs(absolute_total), credit=absolute_total < 0))
    return txml


def rows_groups_btws_totals(rowset, includes_btw=True):
    group_valuebtw = defaultdict(lambda: defaultdict(lambda: [0., 0., 0., 0.]))

    for row in rowset:
        group_valuebtw[row["group"]][str(row["btw"])][0] += row["prevalue"] - (row["btwvalue"] if includes_btw else 0)
        group_valuebtw[row["group"]][str(row["btw"])][1] += row["btwvalue"]
        group_valuebtw[row["group"]][str(row["btw"])][2] += row.get("value_excl", row["value"])
        group_valuebtw[row["group"]][str(row["btw"])][3] += row.get("value_excl", row["value"]) / (1.0 + row["btw"] / 100.0)
        

    for group, values in group_valuebtw.iteritems():
        for btwt, valuebtw in values.iteritems():
            group_valuebtw[group][btwt][0] = int(round(valuebtw[0]))
            group_valuebtw[group][btwt][1] = int(round(valuebtw[1]))
            group_valuebtw[group][btwt][2] = int(round(valuebtw[2]))
            group_valuebtw[group][btwt][3] = int(round(valuebtw[3]))

    return group_valuebtw
