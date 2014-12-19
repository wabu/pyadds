import re


def uncamel(phrase, sep='-'):
    """
    converts camelcase phrase into seperated lower-case phrase

    Parameters
    ---
    phrase : str
        phrase to convert

    Examples
    ---
    >>> uncamel('HTTPRequestHeader')
        'http-request-header'
    >>> uncamel('StatusCode404', sep=' ')
        'status code 404'
    """
    return re.sub(r'((?<=[a-z])[A-Z0-9]|(?!^)[A-Z0-9](?=[a-z]))', sep + r'\1', phrase).lower()


def splitcamel(phrase):
    return uncamel(phrase).split('-')


def name_of(obj):
    if isinstance(obj, str):
        return uncamel(obj)
    elif hasattr(obj, 'name'):
        return obj.name
    else:
        cls = obj if isinstance(obj, type) else type(obj)
        return uncamel(cls.__name__)


def abbrev(obj, n=3):
    name = re.sub(r'\W', '', name_of(obj))
    cons = re.findall('[bcdfghjklmnpqrstvwxyz]', name)
    return ''.join(cons[:n])
