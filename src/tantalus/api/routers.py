"""Tantalus api blueprint gen"""
from flask import Blueprint

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
#bp_pos = blueprint_factory('tantalus.pos', '/pos')
bp_conscribo = blueprint_factory('tantalus.conscribo', 'tantalus.api.conscribo', '/conscribo')
bp_financial = blueprint_factory('tantalus.financial', 'tantalus.api.financial', '/financial')

# Import modules to make them register, this needs to be after the blueprint definition
# Otherwise you get an unresolvable circular import
# This is ungodly ugly, TODO: FIX THIS CRAP

import tantalus.api.base
import tantalus.api.product
import tantalus.api.conscribo
import tantalus.api.relation
import tantalus.api.transaction
import tantalus.api.user
import tantalus.api.financial