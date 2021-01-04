# Tantalus

Tantalus is meant to be the next and hopefully somewhat final successor of [Madmin](https://github.com/davidv1992/madmin). 
Its primary purpose is to manage inventory, but it also includes bindings for the Conscribo XML-API, a point-of-sale system and
support for simple ingredient-to-product processes.

## Features

* Fast transaction input.
* As-Correct-As-Possible inventory pricing.
* Price modifiers.
* Conscribo integration.
* Point-of-sale management.
* Missing/Extra inventory tracking and autocorrection.
* Ingredient-to-product processes.

## Directory Structure

```GAP
├─ api/              # Endpoints go here
│  └─ actions/       # If a function is too complex to put into the endpoints it is put here to keep things tidy.
│
├─ appfactory/       # Flask app creation, configuration and middleware
│
├─ static/           # Static CSS/HTML/JS/Images
│
├─ templates/        # Jinja2 templates
│
├─ tantalus_db     # All data models, for use in the Google Appengine NDB
│
├─ pdfworker/        # Invoice creation and sending
│
├─ lib/              # Add all dependency packages from requirements.txt in here
│
├─ appengine_config.py  # Configure dependencies on the appengine
├─ datastore-admin.py   # Configure backups on the appengine
├─ entrypoint.py        # Instantiate the app
├─ worker.py            # The backend worker
└─ sync_requirements.py # Convinience, sync requirements to lib/

```

## Price Calculation

With Tantalus the way prices are calculated differs from madmin in a significant way. There is no separate entity for a product and its inventory. That way, there is no way to tell where a product came from once it is in the database
This makes sense in the way that if you have two bottles of cola, they are interchangeable. Of course, there is a sell-by date, but that kind of micromanagement is beyond the scope of this system and happens "on the floor".
It also makes pricing fairer. The price of an amount of a certain product is just the fraction of the total amount times the total value. This means that no rounding errors can get lost in the system and that if you buy
items on offer the price is reduced for all items you have, instead of it being a lottery for the parties who buy from you.

## Modifying Transactions

In madmin transactions were basically immutable. This caused many problems, since mistakes happen ([pebcak](https://en.wiktionary.org/wiki/PEBCAK)). Therefore IMP moves to the other end of the spectrum. A transaction is editable
in an easy way, invoices get resent and changes are pushed to Conscribo with the press of a button.