import requests
from getpass import getpass
from haikunator import Haikunator
import random
import sys


h = Haikunator()


def check(r, msg):
    try:
        r.raise_for_status()
    except:
        print(msg)
        print(r.json())
        raise e

base = "http://localhost:8000"

if sys.argv == 1:
    username = input("Username: ")
    password = getpass("Password: ")
else:
    username = sys.argv[1]
    password = sys.argv[2]

s = requests.session()

r = s.post(base + "/login.json", json={"username": username, "password": password})
check(r, "Logging in failed")

groups = [h.haikunate(token_length=0) for i in range(20)]
services = [h.haikunate(token_length=0) for i in range(20)]
btwtypes = [random.randint(0, 21) for i in range(4)]
products = []
relations = []

# Send products
for p in range(100):
    r = s.post(base + "/product/add", json={
        "name": h.haikunate(token_length=0),
        "group": random.choice(groups),
        "tag": '',
        "amount": random.randint(10, 1000),
        "value": random.randint(10, 1000),
        "btw": random.choice(btwtypes)
    })
    check(r, "Failed to send product")
    products.append(r.json()['id'])

# Send relations
for rel in range(20):
    r = s.post(base + "/relation/add", json={
        "name": h.haikunate(token_length=0),
        "budget": random.randint(-10000, 10000),
        "email": '',
        "has_budget": True,
        "send_mail": False,
        "address": '',
        "reference": True
    })
    check(r, "Failed to send relation")
    relations.append(r.json()['id'])

# Send transactions
for rel in range(300):
    r = s.post(base + "/transaction/add", json={
        "relation": random.choice(relations),
        "deliverydate": "{:04d}-{:02d}-{:02d}".format(2020, random.randint(1,12), random.randint(1,27)),
        "description": h.haikunate(token_length=0),
        "sell": [{
            "id": random.choice(products),
            "amount": random.randint(1, 100),
            } for i in range(random.randint(4, 50))],
        "buy": [{
            "id": random.choice(products),
            "amount": random.randint(1, 100),
            "price": random.randint(100, 10000)
        } for i in range(random.randint(4, 50))],
        "service": [{
            "contenttype": random.choice(services),
            "amount": random.randint(1, 100),
            "price": random.randint(10, 100000),
            "btw": random.choice(btwtypes)
        } for i in range(random.randint(4, 50))]
    })
    check(r, "Failed to send transaction")