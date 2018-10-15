import re
from datetime import datetime

from lxml import etree


def parse_result(xml):
    return etree.XML(xml)


def pretty_print(res):
    print(etree.tostring(res, pretty_print=True, encoding='unicode'))


class Result(object):
    def __init__(self, xml):
        tree = etree.fromstring(bytes(xml))
        self.root = tree

    @property
    def success(self):
        return self.root.xpath("success")[0].text == "1"

    @property
    def notifications(self):
        return [child.text for child in self.root.xpath("notifications/notification")]

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
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
               + etree.tostring(etree.ElementTree(self.request)).decode()


class AuthenticateRequest(Request):
    def __init__(self, key, passphrase):
        super(AuthenticateRequest, self).__init__("authenticate", apiIdentifierKey=key, passPhrase=passphrase)


class AuthenticateResult(Result):
    @property
    def sessionId(self):
        return self.root.xpath("sessionId")[0].text


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
        return [TransactionXML(transaction) for transaction in self.root.xpath("transactions/transaction")
                if self.is_interesting_transaction(transaction)]

    @staticmethod
    def is_interesting_transaction(transaction):
        regexp = r"T\#\[\d*\]"
        return re.search(regexp, transaction.xpath("description")[0].text) is not None


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
            self.description = re.sub(regexp, "", self.node.xpath("description")[0].text)
            self.identifier = int(re.search(regexp, self.node.xpath("description")[0].text).group(1))
            self.date = datetime.strptime(self.node.xpath("date")[0].text, "%Y-%m-%d").date()
            self.rows = [TransactionXMLRow(row) for row in self.node.xpath("transactionRows")[0]]
            self.reference = self.rows[0].reference
            self.transactionid = int(self.node.xpath("transactionId")[0].text)

    def toxml(self):
        transaction = etree.Element("transaction")

        if self.transactionid is not None:
            etree.SubElement(transaction, "transactionId").text = str(self.transactionid)

        etree.SubElement(transaction, "description").text = "{}\nTantalus ID: T#[{}]".format(self.description, self.identifier)
        etree.SubElement(transaction, "date").text = self.date.strftime("%Y-%m-%d")

        xmlrows = etree.SubElement(transaction, "transactionRows")
        for row in self.rows:
            row.toxml("{}".format(self.reference), xmlrows)

        return transaction

    def __eq__(self, other):
        return other.identifier == self.identifier


class TransactionXMLRow:
    def __init__(self, node=None, amount=0, account=999, credit=True, vatcode="", vat=0):
        if node is not None:
            self.amount = int(100 * float(node.xpath("amount")[0].text.replace(',', '.')))
            self.credit = node.xpath("side")[0].text == "credit"
            self.account = int(node.xpath("accountNr")[0].text)
            self.reference = node.xpath("reference")[0].text
            self.vatCode = node.xpath("vatCode")[0].text
            self.vatAmount = int(node.xpath("vatAmount")[0].text)
        else:
            self.amount = amount
            self.credit = credit
            self.account = account
            self.reference = ""
            self.vatAmount = vat
            self.vatCode = vatcode

    def toxml(self, reference, addto):
        node = etree.SubElement(addto, "transactionRow")
        etree.SubElement(node, "amount").text = "{:.2f}".format(float(self.amount) / 100).replace('.', ',')
        etree.SubElement(node, "side").text = "credit" if self.credit else "debet"
        etree.SubElement(node, "accountNr").text = str(self.account)
        etree.SubElement(node, "reference").text = reference
        etree.SubElement(node, "vatCode").text = self.vatCode
        etree.SubElement(node, "vatAmount").text = str(self.vatAmount)

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
        return [AccountXML(account) for account in self.root.xpath("accounts/account")]


class AccountXML:
    def __init__(self, node):
        self.account = int(node.xpath("accountNr")[0].text)
        self.name = node.xpath("accountName")[0].text
        self.result = node.xpath("type")[0].text == "result"

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
            transaction.transactionid = int(self.root.xpath("transactionId")[0].text)


class ListVatCodesRequest(Request):
    def __init__(self, date=None):
        super(ListVatCodesRequest, self).__init__("listVatCodes")
        if date is None:
            date = datetime.now().date()
        etree.SubElement(self.request, "date").text = date.strftime("%Y-%m-%d")


class ListVatCodeResult(Result):
    def __init__(self, data):
        super(ListVatCodeResult, self).__init__(data)

