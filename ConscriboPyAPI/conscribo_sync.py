from collections import defaultdict
from google.appengine.ext import ndb

from conscribo_api import Conscribo
from conscribo_mapper import TransactionXML, TransactionXMLRow, ResultException

from ndbextensions.models import TypeGroup
from ndbextensions.conscribo import ConscriboGroupLink, ConscriboRelationLink, ConscriboModLink, ConscriboTransactionLink
from ndbextensions.config import Config



@ndb.transactional(xg=True)
def sync_transactions(transactions):
    config = Config.get_config()
    conscribo = Conscribo(config.conscribo_api_url, config.conscribo_api_key, config.conscribo_api_secret)
    
    for t in transactions:
        link = ConscriboTransactionLink.query(ConscriboTransactionLink.transaction == t.key, ancestor=TypeGroup.conscribo_ancestor()).get()
        if link is None:
            continue
        xml = transaction_to_transactionXML(t, link, config.conscribo_todo_account)
        
        try:
            conscribo.add_change_transaction(xml)
            link.pushed_revision = t.revision
            link.feedback = "Succeeded"
        except ResultException as e:
            link.feedback = str(e)
        link.put()
            
        

def transaction_to_transactionXML(transaction, conscribo_link, todo_account):
    """"Convert a Tantalus Transaction to a Conscribo XML Transaction"""
    txml = TransactionXML(conscribo_link.conscribo_reference,
                          reference="{} {}".format(transaction.relation.get().name, transaction.reference),
                          description=transaction.description)
    txml.date = conscribo_link.bookdate or transaction.deliverydate

    rel_link = ConscriboRelationLink.get_by_relation(transaction.relation)
    
    if rel_link is None:
        total_account = todo_account
    else:   
        total_account = rel_link.linked
        
    txml.rows.append(TransactionXMLRow(account=total_account, amount=abs(transaction.total),
                                       credit=transaction.total < 0))
    
    for group, amount in rows_groups_totals(transaction.one_to_two).iteritems():
        link = ConscriboGroupLink.get_by_group(group)
        if link is None:
            account = todo_account
        else:
            account = link.linked
        txml.rows.append(TransactionXMLRow(account=account, amount=amount, credit=True))
        txml.description += "\nSell Group total {} with value {:.2f}.".format(group.get().name, amount/100.0)
    
    for mod, amount in rows_mods_totals(transaction.one_to_two).iteritems():
        link = ConscriboModLink.get_by_mod(mod)
        if link is None:
            account = todo_account
        else:
            account = link.linked
        txml.rows.append(TransactionXMLRow(account=account, amount=amount, credit=True))
        txml.description += "\nSell Modifier total {} with value {:.2f}.".format(mod.get().name, amount/100.0)
        
    for group, amount in rows_groups_totals(transaction.two_to_one).iteritems():
        link = ConscriboGroupLink.get_by_group(group)
        if link is None:
            account = todo_account
        else:
            account = link.linked
        txml.rows.append(TransactionXMLRow(account=account, amount=amount, credit=False))
        txml.description += "\nBuy Group total {} with value {:.2f}.".format(group.get().name, -amount/100.0)
            
    for mod, amount in rows_mods_totals(transaction.two_to_one).iteritems():
        link = ConscriboModLink.get_by_mod(mod)
        if link is None:
            account = todo_account
        else:
            account = link.linked
        txml.rows.append(TransactionXMLRow(account=account, amount=amount, credit=False))
        txml.description += "\nBuyModifier total {} with value {:.2f}.".format(mod.get().name, -amount/100.0)
        
    for service in transaction.services:
        txml.rows.append(TransactionXMLRow(account=todo_account, amount=abs(service.value), credit=service.value>0))
        txml.description += "\nService {} with value {:.2f}.".format(service.service, service.amount/100.0)
        
    return txml 
        

# All functions below rely on the fact that ndb.Key is a hashable type 
# and can be used as a dictionary key
    
def rows_mods_totals(rowset):
    mods = defaultdict(int)
    for row in rowset:
        for i, mod in enumerate(row.mods):
            mods[mod] += row.modamounts[i] 
    return mods
 
    
def rows_groups_totals(rowset):
    groups_pretotal = defaultdict(int)
    #groups_postotal = defaultdict(int)
    for row in rowset:
        group = row.product.get().group
        groups_pretotal[group] += row.value
        #group_postotal[row.group] += row.value
        for i, mod in enumerate(row.mods):
            if mod.get().modifies:
                groups_pretotal[group] -= row.modamounts[i]
            #else
            #    group_postotal[row.group] += row.modtotals[i]
                
    return groups_pretotal  #, groups_postotal    
