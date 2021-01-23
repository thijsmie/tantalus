import requests
from getpass import getpass


# Steps:
# Create new app
# Deploy project (don't forget index.yaml)
# Activate DataStore
# Default user account admin:AdminAdmin
# Make one request
# Edit config
# Run this script
# Copy over conscribo config

base_old = "https://tantalus-2019.appspot.com"
base_new = "https://tantalus-2020.appspot.com"

old_user = input("old user: ")
old_pass = getpass("old pass: ")

new_user = input("new user: ")
new_pass = ""

if new_user == "":
    new_user = old_user
    new_pass = old_pass
else:
    new_pass = getpass("new pass: ")

so = requests.session()
sn = requests.session()

# log in to old service
r = so.post(base_old + "/login.json", json={"username": old_user, "password": old_pass})
try:
    r.raise_for_status()
except Exception as e:
    print("Logging in on old service failed")
    print(r.json()['error'])
    raise e

# log in to new service
r = sn.post(base_new + "/login.json", json={"username": new_user, "password": new_pass})
try:
    r.raise_for_status()
except Exception as e:
    print("Logging in on new service failed")
    print(r.json()['error'])
    raise e

"""
# Get products
r = so.get(base_old + "/product.json")
r.raise_for_status()
products = r.json()

# Get groups
r = so.get(base_old + "/product/group.json")
r.raise_for_status()
groups = {v['id']: v['name'] for v in r.json()}

# Get btwtypes
r = so.get(base_old + "/product/btwtype.json")
r.raise_for_status()
btwtype = {v['id']: v['percentage'] for v in r.json()}

# Send products
for p in products:
    r = sn.post(base_new + "/product/add", json={
        "name": p['contenttype'],
        "group": groups[p['group']],
        "tag": p['tag'],
        "amount": p['amount'],
        "value": p['value'],
        "btw": btwtype[p['btwtype']] 
    })
    r.raise_for_status()
"""
# Get relations
r = so.get(base_old + "/relation.json")
r.raise_for_status()
relations = r.json()

for rel in relations:
    r = sn.post(base_new + "/relation/add", json={
        "name": rel["name"],
        "budget": rel["budget"],
        "email": rel["email"],
        "has_budget": rel['has_budget'],
        "send_mail": rel['send_mail'],
        "address": rel['address'],
        "reference": rel['numbered_reference']
    })

    try:
        r.raise_for_status()
    except Exception as e:
        print(r.json())
        raise e
