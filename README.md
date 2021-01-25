# Tantalus

Tantalus is meant to be the next and hopefully somewhat final successor of [Madmin](https://github.com/davidv1992/madmin).
Its primary purpose is to manage inventory, but it also includes bindings for the Conscribo XML-API, a point-of-sale system and
several financial tools to make the life of the treasurer of Tartarus easier.

If you would like to deploy this system for your own non-profit association and require assistance you can reach out to me. See my [website](https://tmiedema.com) for ways to contact me. If you want to use this system in a for-profit setting we can discuss rates ;).

## Features

* Enter transactions with an assisting system to speed up this labour-intensive task.
* Automated invoicing.
* Inventory monitoring.
* Conscribo integration.
* Point-of-sale endpoints.

## Directory Structure

```GAP
├─ pos_endpoint/        # This folder contains the POS endpoint client
├─ scripts/             # Helper scripts that interact with the system or help migrating
└─ src/                 # Source code
   ├─  config/            # Config system that gathers parameters from the shell environment
   ├─  ConscriboPyAPI/    # Conscribo Python API bindings
   ├─  tantalus/          # Actual application code
   |   ├─  web/             # Web endpoints
   |   ├─  logic/           # Business logic
   |   ├─  app/             # Application wiring and middleware
   |   ├─  static/          # Static files like images and CSS
   |   └─  templates/       # Jinja2 HTML templates
   ├─  tantalus_db/       # SQLAlchemy models for DB connection
   └─  worker/            # Background worker for async tasks like email and invoicing

```

## Workflow

The core of the Tantalus system is a list of products, each with an amount in stock and price which you sell it for, including VAT. Normal edits to these Products happen through Transactions. When you add a Transaction to the system you can buy products for a specified price and you can sell products for the system-determined price. A Transaction can also include a Service, which is anything that does not relate to a Product tracked by Tantalus.

Tantalus also has Point-of-Sale endpoints. These represent individual products being sold that should not generate an invoice but should be tracked. Turn these into transactions with intervals that are convinient to your usecase.

## Price Calculation

With Tantalus the way prices are calculated differs from madmin in a significant way. There is no separate entity for a product and its inventory. That way, there is no way to tell where a product came from once it is in the database. This makes sense in the way that if you have two bottles of cola, they are interchangeable. Of course, there is a sell-by date, but that kind of micromanagement is beyond the scope of this system and happens "on the floor". The value on sale is a set price.

You should take care when you modify a price while you still have stock of a product. This means you are also changing the value of total owned product, which should be corrected inside Conscribo too.

## POS client

The folder pos_client contains a python module used to run a pos client that communicates with tantalus over its API. See pos-requirements.txt for the dependencies of the pos client. Run as module: `python -m pos_endpoint`.

## Docker-Compose deployment procedure

Copy variables.example.env to variables.env and modify it to your hearts desire. Also have a check of the volumes in the docker-compose file, you might want to change their location. You can also strip out the pgAdmin and postgres containers if you are deploying those somewhere else. Start all containers with:

```bash
    docker-compose up --build -d
```

Note that all DB tables will be created upon the first http request to the application. After creating the tables there will also be a default user admin with password AdminAdmin, which you will want to change before deploying to production.

## Testdata

The script `populate_with_testdata.py` simulates about a years worth of data in a minute or so. It is very useful for testing. The dev-requirements.txt file shows the dependencies used to run this script.

## Testing (re-)deployment

```bash
    docker-compose down && \
    sudo rm -rf path/to/cache/* && \
    docker-compose up --build -d && \
    python scripts/populate_with_testdata.py admin AdminAdmin
```
