"""
Provides functionality for converting YAML formatted files to JSON.

Specifically, YAML incorporating the YAML Stratus format is handled.

Function Exports:

- load()
- to_json()
- load_as_json()
- load_all()
- load_all_as_json()
"""

import json

from .yamlstratus import YamlStratus

__version__ = '1.0.2'


def load(stream, root_tag='main', include_dirs=None, params=None):
    """
    Parse a YAML stratus stream returning a dictionary

    :param stream: stream over the YAML Stratus document
    :param root_tag: the name of the root node in the document to return
        (default 'main')
    :param include_dirs: list of search paths for includes
    :param params: dictionary of parameter name-values
    :rtype: dictionary
    """
    objs = YamlStratus(include_dirs=include_dirs, params=params).load(stream)
    if root_tag is None:
        return objs
    elif objs is None:
        return None
    elif isinstance(objs, str) and objs == root_tag:
        return {}
    elif not isinstance(objs, dict):
        raise Exception('Root node is not a dictionary')
    elif root_tag in objs:
        return objs[root_tag]
    else:
        return None


def load_all(stream, root_tag='main', include_dirs=None, params=None):
    """
    Stream in multiple documents in YAML Stratus format returning an iterator
    that yields corresponding dictionaries

    :param stream: stream over the YAML Stratus document
    :param root_tag: the name of the root node in the document to return
        (default 'main')
    :param include_dirs: list of search paths for includes
    :param params: dictionary of parameter name-values
    :rtype: iterator over dictionaries
    """
    for objs in YamlStratus(include_dirs=include_dirs, params=params).load_all(
            stream):
        if root_tag is None:
            yield objs
        elif objs is None:
            yield None
        elif isinstance(objs, str) and objs == root_tag:
            yield {}
        elif not isinstance(objs, dict):
            raise Exception('Root node is not a dictionary {0}'.format(objs))
        elif root_tag in objs:
            yield objs[root_tag]
        else:
            raise Exception(
                'No node marked "{0}" in document root'.format(root_tag))


def to_json(objs):
    """
    Convenience method for returning am object as JSON

    :param objs: any python dictionary though meant for one generated
        by YamlStratus
    :rtype: string in JSON format
    """
    return json.dumps(objs, sort_keys=True, indent=4, separators=(',', ': '))


def load_as_json(stream, root_tag='main', include_dirs=None, params=None):
    """
    Stream in YAML Stratus stream and returning as JSON

    :param stream: stream over the YAML Stratus document
    :param root_tag: the name of the root node in the document to return
        (default 'main')
    :param include_dirs: list of search paths for includes
    :param params: dictionary of parameter name-values
    :rtype: string in JSON format
    """
    objs = load(stream, include_dirs=include_dirs, params=params,
                root_tag=root_tag)
    return to_json(objs) if not objs is None else []


def load_all_as_json(stream, include_dirs=None, params=None, root_tag='main'):
    """
    Stream in multiple documents in YAML Stratus format returning as iterator
    yielding corresponding JSON documents

    :param stream: stream over the YAML Stratus document
    :param root_tag: the name of the root node in the document to return
        (default 'main')
    :param include_dirs: list of search paths for includes
    :param params: dictionary of parameter name-values
    :rtype: iterator over JSON formatted strings
    """
    for objs in load_all(stream, include_dirs=include_dirs, params=params,
                         root_tag=root_tag):
        yield to_json(objs)
