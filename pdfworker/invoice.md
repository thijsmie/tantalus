{% macro format_currency(amount) %}{{ "{:.2f}".format(amount / 100.0) }}{% endmacro %}

# Tantalusfactuur

---------------------------------------

Factuur | Olympus Nijmegen  
:------ | ----------------:
Referentie: {{ transaction.name }}.{{ transaction.revision }} | Heyendaalseweg 135
Datum activiteit: {{ transaction.deliverydate }} | 6525 AJ Nijmegen
Factuurdatum: {{ transaction.processeddate }} | olympus@science.ru.nl


{{ transaction.description }}

{% if transaction.sell.rows|length > 0 %}
## Geleverd
Product | Aantal | Basiswaarde | {% for name in transaction.sell.modnames %}{{ name }} | {% endfor %}Totaal
:------------- | ---:| ---:| {% for name in transaction.sell.modnames %}--:| {% endfor %}--:
{% for row in transaction.sell.rows -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.prevalue) }} | {% for modtotal in row.modtotals %}{{ format_currency(modtotal) }} | {% endfor %}{{ format_currency(row.total) }}
{% endfor -%}
**Totaal** | | *{{ format_currency(totals.sellprevalue) }}* | {% for total in totals.sellmods %}*{{ format_currency(total) }}* | {% endfor %}*{{ format_currency(totals.selltotal) }}*

{% endif %}
{% if transaction.buy.rows|length > 0 %}
## Retour
Product | Aantal | {% for name in transaction.buy.modnames %}{{ name }} | {% endfor %}Totaal
:------------- | ---:| {% for name in transaction.buy.modnames %}--:| {% endfor %}--:
{% for row in transaction.buy.rows -%}
{{ row.contenttype }} | {{ row.amount }} | {% for modtotal in row.modtotals %}{{ format_currency(modtotal) }} | {% endfor %}{{ format_currency(row.total) }}
{% endfor -%}
**Totaal** | | {% for total in totals.buymods %}*{{ format_currency(total) }}* | {% endfor %}*{{ format_currency(totals.buytotal) }}*

{% endif %}
{% if transaction.service.rows|length > 0 %}
## Services
Product | Aantal | Totaal
:------------- | ---:| ---:
{% for row in transaction.service.rows -%}
{{ row.contenttype }} | {{ row.amount }} | {{ format_currency(row.value) }}
{% endfor -%}
**Totaal** | | *{{ format_currency(totals.servicetotal) }}*

{% endif %}
### Factuurtotaal: &euro;{{ format_currency(totals.selltotal + totals.servicetotal - totals.buytotal) }}
{% if budget %}
Het factuurtotaal is afgeschreven van uw borrelsaldo, wat na deze factuur nog &euro;{{ format_currency(budget)}} bedraagd. Extra borrelsaldo kan overgemaakt worden naar rekeningnummer NL19 ABNA 0448 1916 28 t.n.v. Olympus te Nijmegen.
{% else %}
Wij verzoeken uw vriendelijk om het verschuldigde bedrag binnen 30 dagen over te maken onder vermelding van de referentie naar rekeningnummer NL19 ABNA 0448 1916 28 t.n.v. Olympus te Nijmegen.
{% endif %}