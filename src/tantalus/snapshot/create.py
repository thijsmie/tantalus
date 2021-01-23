from tantalus_db.base import db
from tantalus_db.utility import transactional
from tantalus_db.models import Group, Relation, BtwType, Product, Transaction
from tantalus_db.snapshot import Snapshot, GroupSnapshot, BtwTypeSnapshot, RelationSnapshot, ProductSnapshot, \
    TransactionLineSnapshot, ServiceLineSnapshot, TransactionSnapshot

from config import config


def db_preload(instance):
    db.session.add(instance)
    db.session.flush()
    db.session.refresh(instance)


@transactional
def create_snapshot(name):
    snapshot = Snapshot(
        name=name,
        yearcode=config.yearcode
    )
    db_preload(snapshot)

    group_id_mapping = {}
    product_id_mapping = {}
    btwtype_id_mapping = {}
    relation_id_mapping = {}

    for group in Group.query.all():
        sn_group = GroupSnapshot(
            snapshot_id=snapshot.id,
            name=group.name
        )
        db_preload(sn_group)
        group_id_mapping[group.id] = sn_group.id

    for relation in Relation.query.all():
        sn_relation = RelationSnapshot(
            snapshot_id=snapshot.id,
            name=relation.name,
            budget=relation.budget
        )
        db_preload(sn_relation)
        relation_id_mapping[relation.id] = sn_relation.id

    for btwtype in BtwType.query.all():
        sn_btwtype = BtwTypeSnapshot(
            snapshot_id=snapshot.id,
            name=btwtype.name,
            percentage=btwtype.percentage
        )
        db_preload(sn_btwtype)
        btwtype_id_mapping[btwtype.id] = sn_btwtype.id

    for product in Product.query.all():
        sn_product = ProductSnapshot(
            snapshot_id=snapshot.id,
            contenttype=product.contenttype,
            tag=product.tag,
            value=product.value,
            amount=product.amount,
            discontinued=product.discontinued,
            group_id=group_id_mapping[product.group_id],
            btwtype_id=btwtype_id_mapping[product.btwtype_id]
        )
        db_preload(sn_product)
        product_id_mapping[product.id] = sn_product.id

    for transaction in Transaction.query.all():
        one_to_two = []
        two_to_one = []
        services = []

        for transactionline in transaction.one_to_two:
            one_to_two.append(TransactionLineSnapshot(
                snapshot_id=snapshot.id,
                product_id=product_id_mapping[transactionline.product_id],
                prevalue=transactionline.prevalue,
                value=transactionline.value,
                btwtype_id=btwtype_id_mapping[transactionline.btwtype_id],
                amount=transactionline.amount
            ))

        for transactionline in transaction.two_to_one:
            two_to_one.append(TransactionLineSnapshot(
                snapshot_id=snapshot.id,
                product_id=product_id_mapping[transactionline.product_id],
                prevalue=transactionline.prevalue,
                value=transactionline.value,
                btwtype_id=btwtype_id_mapping[transactionline.btwtype_id],
                amount=transactionline.amount
            ))

        for service in transaction.services:
            services.append(ServiceLineSnapshot(
                snapshot_id=snapshot.id,
                service=service.service,
                value=service.value,
                amount=service.amount,
                btwtype_id=btwtype_id_mapping[service.btwtype_id]
            ))

        sn_transaction = TransactionSnapshot(
            snapshot_id=snapshot.id,
            reference=transaction.reference,
            informal_reference=transaction.informal_reference,
            revision=transaction.revision,
            deliverydate=transaction.deliverydate,
            processeddate=transaction.processeddate,
            description=transaction.description,
            relation_id=relation_id_mapping[transaction.relation_id],
            one_to_two=one_to_two,
            two_to_one=two_to_one,
            services=services,
            total=transaction.total,
            two_to_one_has_btw=transaction.two_to_one_has_btw,
            two_to_one_btw_per_row=transaction.two_to_one_btw_per_row
        )

        if transaction.conscribo_transaction:
            sn_transaction.conscribo_reference = transaction.conscribo_transaction.reference

        if transaction.relation.has_budget:
            after = Transaction.query.filter(
                Transaction.reference > transaction.reference, 
                Transaction.relation == transaction.relation).all()
            sn_transaction.budget = transaction.relation.budget + sum([t.total for t in after])

        db_preload(sn_transaction)
