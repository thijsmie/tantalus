from tantalus_db.snapshot import ServiceLineSnapshot, GroupSnapshot
from collections import defaultdict


def snapshot_group_values(snapshot):
    return {
        group.name: sum(product.amount * product.value for product in group.products)
            for group in GroupSnapshot.query.filter(GroupSnapshot.snapshot_id == snapshot.id).all()
    }


def snapshot_group_excl_values(snapshot):
    return {
        group.name: sum(product.amount * product.value / (1 + product.btwtype.percentage / 100.0) for product in group.products)
            for group in GroupSnapshot.query.filter(GroupSnapshot.snapshot_id == snapshot.id).all()
    }


def snapshot_service_values(snapshot):
    services = defaultdict(lambda: [0, 0, 0])

    for service in ServiceLineSnapshot.query.filter(ServiceLineSnapshot.snapshot_id == snapshot.id).all():
        value = service.amount * service.value
        services[service.service][0] += value
        if value > 0:
            services[service.service][1] += value
        else:
            services[service.service][2] += value

    return services


def snapshot_service_excl_values(snapshot):
    services = defaultdict(lambda: [0, 0, 0])

    for service in ServiceLineSnapshot.query.filter(ServiceLineSnapshot.snapshot_id == snapshot.id).all():
        value = service.amount * service.value
        services[service.service][0] += value
        if value > 0:
            services[service.service][1] += value
        else:
            services[service.service][2] += value

    return services