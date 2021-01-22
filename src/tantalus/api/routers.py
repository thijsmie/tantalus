"""Tantalus api blueprint gen"""
from flask import Blueprint
from importlib import import_module

blueprints = []


def blueprint_factory(name, import_name, url_prefix):
    """Generates blueprint objects for view modules.
    Positional arguments:
    partial_module_string -- string representing a view module without the absolute path
    url_prefix -- URL prefix passed to the blueprint.
    Returns:
    Blueprint instance for a view module.
    """

    blueprint = Blueprint(name, import_name, url_prefix=url_prefix)
    blueprints.append(blueprint)
    return blueprint


# Create blueprints, can be imported by views
bp_base = blueprint_factory("tantalus", 'tantalus.api.base', '')
bp_product = blueprint_factory("tantalus.product", 'tantalus.api.product', '/product')
bp_relation = blueprint_factory('tantalus.relation', 'tantalus.api.relation', '/relation')
bp_transaction = blueprint_factory('tantalus.transaction', 'tantalus.api.transaction', '/transaction')
bp_user = blueprint_factory('tantalus.user', 'tantalus.api.user', '/user')
bp_pos = blueprint_factory('tantalus.pos', 'tantalus.api.pos', '/pos')
bp_conscribo = blueprint_factory('tantalus.conscribo', 'tantalus.api.conscribo', '/conscribo')
bp_financial = blueprint_factory('tantalus.financial', 'tantalus.api.financial', '/financial')
bp_snapshot = blueprint_factory('tantalus.snapshot', 'tantalus.api.snapshot', '/snapshot')
bp_api = blueprint_factory('tantalus.api', 'tantalus.api.api', '/api')
bp_administration = blueprint_factory('tantalus.administration', 'tantalus.api.administration', '/administration')

bp_pos_client = blueprint_factory('tantalus.pos_client', 'tantalus.api.pos_client', '/poscl')


def activate_routes():
    for blueprint in blueprints:
        import_module(blueprint.import_name)