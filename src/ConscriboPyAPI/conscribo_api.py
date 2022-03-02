from .conscribo_mapper import AuthenticateRequest, AuthenticateResult, TransactionRequest, TransactionResult,\
    ListAccountsRequest, ListAccountsResult, TransactionPutRequest, TransactionPutResult
import requests
from datetime import date


class Conscribo:
    def __init__(self, api_endpoint, api_key, api_passphrase):
        self.s = requests.session()
        self.status = 0
        self.ep = api_endpoint
        self.key = ""
        self.headers = {"X-Conscribo-API-Version": "0.20161212"}
        self.authenticate(api_key, api_passphrase)
        self._accounts = None
        self._transactions = None

    def request(self, request):
        return self.s.post(self.ep, request.get(), headers=self.headers)

    def authenticate(self, api_key, api_passphrase):
        req = AuthenticateRequest(api_key, api_passphrase)
        tod = self.request(req)
        tod.raise_for_status()
        res = AuthenticateResult(tod.content)
        res.raise_for_status()

        self.headers.update({
            "X-Conscribo-SessionId": res.sessionId
        })

    def get_transactions(self):
        req = TransactionRequest()
        req.filterDate(date(2017, 8, 1), date(2017, 8, 1))
        tod = self.request(req)
        tod.raise_for_status()
        res = TransactionResult(tod.content)
        res.raise_for_status()
        self._transactions = res.transactions

    def get_accounts(self):
        req = ListAccountsRequest()
        tod = self.request(req)
        tod.raise_for_status()
        res = ListAccountsResult(tod.content)
        res.raise_for_status()
        self._accounts = res.accounts

    @property
    def transactions(self):
        if self._transactions is None:
            self.get_transactions()
        return self._transactions

    @property
    def accounts(self):
        if self._accounts is None:
            self.get_accounts()
        return self._accounts

    def add_change_transaction(self, transaction):
        toadd = transaction.transactionid is None and self._transactions
        req = TransactionPutRequest(transaction)
        tod = self.request(req)
        tod.raise_for_status()
        res = TransactionPutResult(tod.content, transaction)
        res.raise_for_status()

        if toadd:
            self._transactions.append(transaction)
