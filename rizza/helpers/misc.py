# -*- encoding: utf-8 -*-
"""A module that provides miscellaneous helper functions."""
from inspect import signature
from itertools import combinations, product
from json import loads
from random import randint
from requests import HTTPError
from logzero import logger
from nailgun import entity_mixins


def combination_list(base=None, max_fields=None):
    """Create a list of all combinations from the source list."""
    if not base:
        return []

    if not max_fields:
        max_fields = len(base)

    combo_list = []
    for _ in range(1, max_fields + 1):
        combo_list.extend(
            [combo for combo in combinations(base, _)])

    return combo_list


def product_list(base=None, max_fields=None):
    """Create a list of all products from the source list."""
    if not base or max_fields == 0:
        return []

    if not max_fields:
        max_fields = len(base)

    return [_ for _ in product(base, repeat=max_fields)]


def map_field_inputs(fields, input_list):
    """Map a tuple of fields to a list of input tuples."""
    return [{field: inpt for field, inpt in zip(fields, input_tupe)}
            for input_tupe in input_list]


def dictionary_exclusion(indict=None, exclude=None):
    """Remove any dictionary entries containing the specified string(s)."""
    if exclude:
        if not isinstance(exclude, list):
            exclude = [exclude]
        for exclusion in exclude:
            exclusion = str(exclusion)
            indict = {
                x: y for x, y
                in indict.items()
                if exclusion not in str(x)
                and exclusion not in str(y)
            }
    return indict


def handle_exception(exception=None):
    """Translate an exception into a usable format."""
    if exception.__class__.__name__ in dir(entity_mixins):
        return {'nailgun': exception.__class__.__name__}
    elif isinstance(exception, HTTPError):
        resp = {}
        for name, contents in exception.__dict__.items():
            if '_' not in name:
                if 'json' in dir(contents):
                    try:
                        resp[name] = contents.json()
                    except Exception as err:
                        resp[name] = contents.content
                else:
                    resp[name] = contents
        return {'HTTPError': resp}
    elif 'args' in dir(exception):
        return {exception.__class__.__name__: exception.args}
    else:
        return {'unhandled': str(exception) or 'undefined'}


def json_serial(obj=None):
    """JSON serializer for objects not serializable by default json code."""
    if 'datetime' in str(obj.__class__):
        return obj.isoformat()
    elif obj.__class__.__name__ == 'PreparedRequest':
        return loads(obj.body)
    elif obj.__class__.__name__ == 'Response':
        return {'message': obj.json(), 'status': obj.status_code}
    elif obj.__class__.__name__ == 'PosixPath':
        return str(obj)
    raise TypeError("Type {0} not serializable".format(type(obj)))


def dict_search(needle, haystack):
    if not isinstance(haystack, dict):
        if str(needle) in str(haystack):
            return True
        else:
            return False
    if needle in haystack:
        return True
    for key, value in haystack.items():
        if str(needle) in str(key):
            return True
        if dict_search(needle, value):
            return True
    return False


def field_to_entity(field):
    """Takes in a field name and tries to find an entity that matches"""
    from rizza.entity_tester import EntityTester
    entity_list = EntityTester.pull_entities().keys()
    field = ''.join([x.capitalize() for x in field.split('_')])
    if field in entity_list:
        return field


def get_default_type(func):
    """Return the type of the first default argument for a function or None"""
    parameters = signature(func).parameters
    types = []
    for key in parameters.keys():
        if parameters[key].default:
            types.append(type(parameters[key].default))
    return types


def form_input(name, methods, field, config):
    """Take in a function name, get information, call it, return result"""
    if 'genetic' in name:
        entity = field_to_entity(field)
        if entity:
            return methods.get(
                name, lambda: name)(config, entity)
        else:  # if the entity isn't valid, suggest removing the field
            return '~'
    else:
        types = get_default_type(methods.get(name, lambda: name))
        if types and types[0] == int and types.count(types[0]) == len(types):
            # currently only support integers
            for i in range(len(types)):
                types[i] = randint(1, 20)
            try:
                return methods.get(name, lambda: name)(*types)
            except Exception as err:
                logger.debug(err)
        return methods.get(name, lambda: name)()
