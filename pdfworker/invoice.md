{% macro format_currency(amount) %}{{ "{:.2f}".format(amount / 100.0) }}{% endmacro %}

# Tantalusfactuur

---------------------------------------

Factuur | Stichting Tartarus
:------ | ----------------:
Referentie: {{ transaction.reference }} | 
Informele naam: {{ transaction.name }}.{{ transaction.revision }} | Heyendaalseweg 135
Datum activiteit: {{ transaction.deliverydate }} | 6525 AJ Nijmegen
Factuurdatum: {{ transaction.processeddate }} | tartarus@science.ru.nl

**Afnemer** <br>
{{ relation.address|replace("\n", " <br> ")|safe }}

{{ transaction.description }}

{% if transaction.sell|length > 0 %}
## Geleverd
Product | Aantal | Stukprijs | Totaal | BTW%
:------------- | ---:| ---:| ---:|---:
{% for row in transaction.sell -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.prevalue / row.amount) }} | {{ format_currency(row.prevalue) }} | {{ row.btw }}%
{% endfor -%}
**Totaal** | | | *{{ format_currency(transaction.selltotal) }}* |

{% endif %}
{% if transaction.buy|length > 0 %}
## Retour
Product | Aantal | Stukprijs | Totaal{% if transaction.two_to_one_has_btw %}(Incl. BTW){% else %}(Excl. BTW){% endif %} | BTW% {% if transaction.two_to_one_btw_per_row %}| &euro;BTW{% endif %}
:------------- | ---:| ---:| ---:| ---:{% if transaction.two_to_one_btw_per_row %}| ---:{% endif %}
{% for row in transaction.buy -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.prevalue / row.amount) }} | {{ format_currency(row.prevalue) }} | {{ row.btw }}%{% if transaction.two_to_one_btw_per_row %}| {{ format_currency(row.btwvalue) }}{% endif %}
{% endfor -%}
**Totaal** | | | *{{ format_currency(transaction.buytotal) }}* |

{% endif %}
{% if transaction.service|length > 0 %}
## Services
Product | Aantal | Totaal
:------------- | ---:| ---:
{% for row in transaction.service -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.prevalue) }} | {{ row.btw }}
{% endfor -%}
**Totaal** | | *{{ format_currency(transaction.servicetotal) }}*

{% endif %}
## BTW
BTW% | BTW totaal 
---: | ---:
{% for percentage, value in transaction.btwtotals.items() -%}
{{ percentage }}| {{ format_currency(value) }}
{% endfor %}

## Factuurtotaal
Omschrijving | Bedrag
:---- | ----:
Exclusief BTW | &euro;{{ format_currency(transaction.total - transaction.btwtotal) }}
Totaal BTW | &euro;{{ format_currency(transaction.btwtotal) }}
Eindtotaal | &euro;{{ format_currency(transaction.total) }}

{% if budget %}
Het factuurtotaal is afgeschreven van uw borrelsaldo, wat na deze factuur nog &euro;{{ format_currency(budget)}} bedraagd. Extra borrelsaldo kan overgemaakt worden naar rekeningnummer NL02 ABNA 0800 2042 55 t.n.v. Sticthing Tartarus te Nijmegen.
{% else %}
Wij verzoeken uw vriendelijk om het verschuldigde bedrag binnen 30 dagen over te maken onder vermelding van de referentie naar rekeningnummer NL02 ABNA 0800 2042 55 t.n.v. Sticthing Tartarus te Nijmegen.
{% endif %}
BTW: NL 858068199 B 01, KvK: 69928622
