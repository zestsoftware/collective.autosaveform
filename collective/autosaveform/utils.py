def deep_seek(data, keys, default_value = None):
    """ Simple access to nested dictionaries.
    For example the following dictionary:
    >>> d = {'a': {'a': 1},
    ...      'b': {'a': 2,
    ...            'b': 3}}

    >>> deep_seek(d, ['b', 'b'])
    3

    It is equivalent to:
    >>> d['b']['b']
    3

    But you can specify default values when
    trying to access inexisting values:
    >>> deep_seek(d, ['a', 'b', 'c'], 'Ouch :/')
    'Ouch :/'
    
    >>> d['a']['b']['c']
    Traceback (most recent call last):
    ...
    KeyError: 'b'

    """
    d = data
    for key in keys[:-1]:
        d = d.get(key, {})

    return d.get(keys[-1], default_value)
