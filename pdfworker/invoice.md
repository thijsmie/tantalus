{% macro format_currency(amount) %}{{ "{:.2f}".format(amount / 100.0).replace(".",",") }}{% endmacro %}

# Tantalusfactuur

---------------------------------------

Factuur | Stichting Tartarus
:------ | ----------------:
Referentie: 1819-{{ transaction.reference }} | Heyendaalseweg 135
Informele naam: {{ transaction.name }}.{{ transaction.revision }} | 6525 AJ Nijmegen
Datum activiteit: {{ transaction.deliverydate }} | tartarus@science.ru.nl
Factuurdatum: {{ transaction.processeddate }} | BTW: NL 858068199 B 01, KvK: 69928622

**Afnemer** <br>
{{ relation.address|replace("\n", " <br> ")|safe }}

{{ transaction.description }}

{% if transaction.sell|length > 0 %}
## Geleverd
Product | Aantal | Stukprijs (Incl. BTW) | Totaal (Incl. BTW) | BTW%
:--------------------------- | ---:| ---:| ---:|---:
{% for row in transaction.sell -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.prevalue / row.amount) }} | {{ format_currency(row.prevalue) }} | {{ row.btw }}%
{% endfor -%}
**Totaal** | | | *{{ format_currency(transaction.selltotal) }}* |

{% endif %}
{% if transaction.buy|length > 0 %}
## Retour
Product | Aantal | Stukprijs | Totaal{% if transaction.two_to_one_has_btw %}(Incl. BTW){% else %}(Excl. BTW){% endif %} | BTW% {% if transaction.two_to_one_btw_per_row %}| &euro;BTW{% endif %}
:--------------------------- | ---:| ---:| ---:| ---:{% if transaction.two_to_one_btw_per_row %}| ---:{% endif %}
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
BTW% | Bedrag Exclusief | BTW totaal | Bedrag Inclusief 
---: | ---: | ---: | ---:
{% for percentage, value in transaction.btwtotals.items() -%}
{{ percentage }} | {{ format_currency(-transaction.btwvalues[percentage] + value) }} | {{ format_currency(-value) }} | {{ format_currency(-transaction.btwvalues[percentage]) }}
{% endfor %}

## Factuurtotaal
Omschrijving | Bedrag
:---- | ----:
Exclusief BTW | &euro;{{ format_currency(transaction.total + transaction.btwtotal) }}
Totaal BTW | &euro;{{ format_currency(-transaction.btwtotal) }}
Eindtotaal | &euro;{{ format_currency(transaction.total) }}

{% if budget %}
Het factuurtotaal is afgeschreven van uw borrelsaldo, wat na deze factuur nog &euro;{{ format_currency(budget)}} bedraagt. Extra borrelsaldo kan overgemaakt worden naar rekeningnummer NL02 ABNA 0800 2042 55 t.n.v. Stichting Tartarus te Nijmegen.
{% else %}
Wij verzoeken u vriendelijk om het verschuldigde bedrag binnen 30 dagen over te maken onder vermelding van de referentie naar rekeningnummer NL02 ABNA 0800 2042 55 t.n.v. Stichting Tartarus te Nijmegen.
{% endif %}

