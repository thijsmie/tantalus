from tantalus.appfactory.auth import current_user
from tantalus_db.base import db
from tantalus_db.models import PosProduct, PosEndpoint, PosSale
from tantalus_db.utility import transactional

from tantalus.logic.btwtype import get_btwtype


@transactional
def new_pos_product(data):
    s = PosProduct(
        name=data['name'],
        product_id=int(data['product']),
        scan_id=data.get('scan_id', ''),
        keycode=data.get('keycode', '')
    )
    db.session.add(s)
    return s


@transactional
def edit_pos_product(posproduct, data):
    assert not posproduct.is_service

    posproduct.name = data.get('name', posproduct.name)
    posproduct.product_id = data.get('product', posproduct.product_id)
    posproduct.scan_id = data.get('scan_id', posproduct.scan_id),
    posproduct.keycode = data.get('keycode', posproduct.scan_id)


@transactional
def new_pos_service(data):
    s = PosProduct(
        name=data['name'],
        service=data['service'],
        service_btw=get_btwtype(data['btw']),
        service_price=data['price'],
        scan_id=data.get('scan_id', ''),
        keycode=data.get('keycode', '')
    )
    db.session.add(s)
    return s


@transactional
def edit_pos_service(posproduct, data):
    assert posproduct.is_service

    posproduct.name = data.get('name', posproduct.name)
    posproduct.service = data.get('service', posproduct.service)
    posproduct.service_btw = get_btwtype(
        data['btw']) if 'btw' in data else posproduct.service_btw
    posproduct.service_price = data.get('price', posproduct.service_price)
    posproduct.scan_id = data.get('scan_id', posproduct.scan_id),
    posproduct.keycode = data.get('keycode', posproduct.scan_id)


@transactional
def discontinue_pos_product(posproduct):
    posproduct.discontinued = True


@transactional
def add_pos_endpoint(data):
    endpoint = PosEndpoint(
        name=data['name'],
        relation_id=int(data['relation'])
    )
    db.session.add(endpoint)
    return endpoint


@transactional
def new_pos_sale(data):
    endpoint = PosEndpoint.query.get(data['endpoint'])
    product = PosProduct.query.get(data['product'])

    price = product.service_price if product.is_service else product.product.value
    btwtype = product.service_btw if product.is_service else product.product.btwtype

    sale = PosSale(
        posendpoint=endpoint,
        posproduct=product,
        amount=data['amount'],
        unit_price=price,
        btwtype=btwtype,
        user=current_user.user
    )
    db.session.add(sale)
    return sale