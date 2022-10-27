import re
import logging
from datetime import datetime
from xml.etree import ElementTree as etree
from unidecode import unidecode


class Result(object):
    def __init__(self, xml):
        logging.info(xml)
        tree = etree.fromstring(bytes(xml))
        self.root = tree

    @property
    def success(self):
        return self.root.findall("success")[0].text == "1"

    @property
    def notifications(self):
        return [child.text for child in self.root.findall("notifications/notification")]

    def raise_for_status(self):
        if not self.success:
            raise ResultException(self.notifications)


class ResultException(Exception):
    def __init__(self, notifications):
        msg = "API exception(s) occurred:\n" + "\n".join(notifications)
        super(ResultException, self).__init__(msg)


class Request(object):
    def __init__(self, command, **kwargs):
        self.request = etree.Element("request")
        etree.SubElement(self.request, "command").text = command

        for k, v in kwargs.items():
            if v is not None:
                etree.SubElement(self.request, k).text = v

    def get(self):
        e = self._get()
        logging.info(e)
        return e

    def _get(self):
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
               + etree.tostring(self.request, encoding='unicode')


class AuthenticateRequest(Request):
    def __init__(self, key, passphrase):
        super(AuthenticateRequest, self).__init__("authenticateWithUserAndPass", userName=key, passPhrase=passphrase)


class AuthenticateResult(Result):
    @property
    def sessionId(self):
        return self.root.findall("sessionId")[0].text


class TransactionRequest(Request):
    def __init__(self, limit=None, offset=None):
        super(TransactionRequest, self).__init__("listTransactions", limit=limit, offset=offset)
        self.filters = etree.SubElement(self.request, "filters")

    def filterDate(self, date_start=None, date_end=None):
        f = etree.SubElement(self.filters, "filter")
        if date_start is not None:
            etree.SubElement(f, "dateStart").text = date_start.strftime("%Y-%m-%d")
        if date_end is not None:
            etree.SubElement(f, "dateEnd").text = date_end.strftime("%Y-%m-%d")


class TransactionResult(Result):
    @property
    def transactions(self):
        return [TransactionXML(transaction) for transaction in self.root.findall("transactions/transaction")
                if self.is_interesting_transaction(transaction)]

    @staticmethod
    def is_interesting_transaction(transaction):
        regexp = r"T\#\[\d*\]"
        return re.search(regexp, transaction.findall("description")[0].text) is not None


class TransactionXML:
    def __init__(self, node_or_id, reference="", description=""):
        if type(node_or_id) == int:
            self.identifier = node_or_id
            self.reference = reference
            self.description = description
            self.date = datetime.now().date()
            self.rows = []
            self.transactionid = None
        else:
            self.node = node_or_id
            regexp = r"Tantalus ID\:\s*T\#\[(\d*)\]"
            self.description = re.sub(regexp, "", self.node.findall("description")[0].text)
            self.identifier = int(re.search(regexp, self.node.findall("description")[0].text).group(1))
            self.date = datetime.strptime(self.node.findall("date")[0].text, "%Y-%m-%d").date()
            self.rows = [TransactionXMLRow(row) for row in self.node.findall("transactionRows")[0]]
            self.reference = self.rows[0].reference
            self.transactionid = int(self.node.findall("transactionId")[0].text)

    def toxml(self):
        transaction = etree.Element("transaction")

        if self.transactionid is not None:
            etree.SubElement(transaction, "transactionId").text = str(self.transactionid)

        etree.SubElement(transaction, "description").text = "{}\nTantalus ID: T#[{}]".format(unidecode(self.description), self.identifier)
        etree.SubElement(transaction, "date").text = self.date.strftime("%Y-%m-%d")

        xmlrows = etree.SubElement(transaction, "transactionRows")
        for row in self.rows:
            row.toxml("{}".format(self.reference), xmlrows)

        return transaction

    def __eq__(self, other):
        return other.identifier == self.identifier


def int_to_money(x):
    s = str(int(x))
    if len(s) > 2:
        return f"{s[:-2]},{s[-2:]}"
    elif len(s) == 2:
        return f"0,{s}"
    elif len(s) == 1:
        return f"0,0{s}"


def money_to_int(s):
    if ',' not in s:
        return int(s) * 100
    if s[-1] == ',':
        return int(s[:-1])
    if s[-2] == ',':
        return int(f"{s[:-2]}{s[-1]}") * 10
    if s[-3] == ',':
        return int(f"{s[:-3]}{s[-2]}{s[-1]}")


class TransactionXMLRow:
    def __init__(self, node=None, amount=0, account=999, credit=True, vatcode="", vat=0):
        if node is not None:
            self.credit = node.findall("side")[0].text == "credit"
            self.account = int(node.findall("accountNr")[0].text)
            self.reference = node.findall("reference")[0].text
            self.vatCode = node.findall("vatCode")[0].text
            self.vatAmount = money_to_int(node.findall("vatAmount")[0].text)
            self.amount = money_to_int(node.findall("amount")[0].text) - self.vatAmount
        else:
            self.amount = amount
            self.credit = credit
            self.account = account
            self.reference = ""
            self.vatAmount = vat
            self.vatCode = vatcode

    def toxml(self, reference, addto):
        node = etree.SubElement(addto, "transactionRow")
        etree.SubElement(node, "amount").text = int_to_money(self.amount + self.vatAmount)
        etree.SubElement(node, "side").text = "credit" if self.credit else "debet"
        etree.SubElement(node, "accountNr").text = str(self.account)
        etree.SubElement(node, "reference").text = reference
        if self.vatCode != "":
            etree.SubElement(node, "vatCode").text = self.vatCode
            etree.SubElement(node, "vatAmount").text = int_to_money(self.vatAmount)

    def __repr__(self):
        return "{} to {} {}".format(self.amount, self.account, "Credit" if self.credit else "Debet")

    def __str__(self):
        return self.__repr__()


class ListAccountsRequest(Request):
    def __init__(self, date=None):
        super(ListAccountsRequest, self).__init__("listAccounts")
        if date is None:
            date = datetime.now().date()
        etree.SubElement(self.request, "date").text = date.strftime("%Y-%m-%d")


class ListAccountsResult(Result):
    @property
    def accounts(self):
        return [AccountXML(account) for account in self.root.findall("accounts/account")]


class AccountXML:
    def __init__(self, node):
        self.account = int(node.findall("accountNr")[0].text)
        self.name = node.findall("accountName")[0].text
        self.result = node.findall("type")[0].text == "result"

    def __repr__(self):
        return "{} {}[{}]".format("Result" if self.result else "Balance", self.name, self.account)

    def __str__(self):
        return str(self.account)

    def __int__(self):
        return self.account


class TransactionPutRequest(Request):
    def __init__(self, transaction):
        super(TransactionPutRequest, self).__init__("addChangeTransaction")
        self.request.extend(transaction.toxml())


class TransactionPutResult(Result):
    def __init__(self, data, transaction):
        super(TransactionPutResult, self).__init__(data)
        if self.success:
            transaction.transactionid = int(self.root.findall("transactionId")[0].text)


class ListVatCodesRequest(Request):
    def __init__(self, date=None):
        super(ListVatCodesRequest, self).__init__("listVatCodes")
        if date is None:
            date = datetime.now().date()
        etree.SubElement(self.request, "date").text = date.strftime("%Y-%m-%d")


class ListVatCodeResult(Result):
    def __init__(self, data):
        super(ListVatCodeResult, self).__init__(data)

