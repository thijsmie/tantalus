from tantalus_db.base import db
from tantalus_db.models import ServiceLine
from collections import defaultdict


def service_values():
    services = defaultdict(lambda: [0, 0, 0])

    for service in ServiceLine.query.all():
        value = service.amount * service.value
        services[service.service][0] += value
        if value > 0:
            services[service.service][1] += value
        else:
            services[service.service][2] += value

    return services


def service_excl_values():
    services = defaultdict(lambda: [0, 0, 0])

    for service in ServiceLine.query.all():
        value = service.amount * service.value
        services[service.service][0] += value
        if value > 0:
            services[service.service][1] += value
        else:
            services[service.service][2] += value

    return services