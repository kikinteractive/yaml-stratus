#!/usr/bin/env python

"""
Provides functionality for converting YAML formatted files to JSON.

Specifically, YAML incorporating the YAML Stratus format is handled.

Class Exports:

- YamlStratusLoader
- YamlStratus
"""

import base64
import os.path

import yaml


class MergeNode(object):
    """Represents a node in YAML document being merged"""

    def __init__(self, starting_from, merge_with):
        self.starting_from = starting_from
        self.merge_with = merge_with
        self.is_merged = False
        # The result of the merge should be typed like the starting node
        self.target = [] if isinstance(starting_from, list) or isinstance(
            starting_from, str) else dict()


class YamlStratusLoader(yaml.Loader):
    """
    Custom loader for handling custom extensions
    """

    def __init__(self, stream, params, include_dirs):
        super(YamlStratusLoader, self).__init__(stream)
        self.include_dirs = include_dirs or []
        self.merge_nodes = []
        self.removed_node = object()
        self.replaced_nodes = []
        self.params_dict = params or dict()

    @staticmethod
    def __check_include_file(directory, filename):
        """
        For finding include file in given directory. Tries various suffixes
        and no suffix
        """
        path = os.path.join(directory, filename) + '.yaml'
        if os.path.exists(path):
            return path
        path = os.path.join(directory, filename) + '.yml'
        if os.path.exists(path):
            return path
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
        return None

    def __find_include_file(self, filename):
        """Searches for file in the include path"""
        path = None
        if self.include_dirs is None or len(self.include_dirs) == 0:
            path = YamlStratusLoader.__check_include_file('.', filename)
        else:
            for include_dir in self.include_dirs:
                path = YamlStratusLoader.__check_include_file(include_dir,
                                                              filename)
                if path is not None:
                    break
        if path is None:
            raise Exception("Cannot find {0}".format(filename))
        return path

    def include(self, node):
        """
        Extension that handles including of other yaml files
        """
        name = self.construct_scalar(node)

        index = name.find('.')

        if index == -1:
            filename = name
            node_name = None
        else:
            filename = name[:index]
            node_name = name[index + 1:]
        path = self.__find_include_file(filename)
        with open(path, 'r') as include_fp:
            included_yaml_stratus = YamlStratus(include_dirs=self.include_dirs,
                                                params=self.params_dict)
            obj = included_yaml_stratus.load(include_fp)
            if node_name is None:
                return obj
            else:
                for node in node_name.split('.'):
                    obj = obj[node]
                return obj

    def include_base64(self, node):
        """
        Extension that handles including of other file as a base64 encoded
        string
        """
        filename = self.construct_scalar(node)

        path = self.__find_include_file(filename)
        with open(path, 'r') as include_fp:
            return base64.b64encode(include_fp.read())

    def remove(self, node):
        """
        Extension for recording nodes for removal during !merge
        process
        """
        return self.removed_node

    def replace(self, node):
        """
        Extension for recording nodes for replacement during !merge
        process
        """
        if isinstance(node, yaml.nodes.SequenceNode):
            node_list = self.construct_sequence(node)
            self.replaced_nodes.append(node_list)
            return node_list
        elif isinstance(node, yaml.nodes.MappingNode):
            mappings = self.construct_mapping(node)
            self.replaced_nodes.append(mappings)
            return mappings
        else:
            raise Exception(
                "Unsupported type for replace extension %s" % type(node))

    def join_text(self, node):
        """
        Extension for recording nodes for replacement during !merge
        process
        """
        text = self.construct_scalar(node)
        parts = [lpart.split("!}") for lpart in text.split("!{")]
        joined = []
        for part in parts:
            if len(part) == 1:
                joined.append(part[0])
            else:
                subloader = YamlStratusLoader(part[0], include_dirs=None,
                                              params=None)
                try:
                    obj = subloader.get_single_data()
                    joined.append(obj)
                finally:
                    subloader.dispose()

                joined.append(part[1])
        return {
            "Fn::Join": [
                "",
                joined
            ]
        }

    # Tag that merges two node to a single node
    # This one seems really useful
    def merge(self, node):
        """
        Extension for merging trees of nodes. Must have exactly two child nodes,
        one called 'startingFrom' and the other called 'mergeWith'.  The tree of
        nodes under 'startingFrom' is merged with the tree of nodes under
        'mergeWith'.

        Note that here we just record the nodes needing merge. The actual merge
        is done in a subsequent pass.
        """
        mappings = self.construct_mapping(node)

        if 'startingFrom' not in mappings:
            raise Exception(
                "!merge extension requires child node 'startingFrom'")
        if 'mergeWith' not in mappings:
            raise Exception("!merge extension requires child node 'mergeWith'")

        merge_node = MergeNode(mappings['startingFrom'], mappings['mergeWith'])

        self.merge_nodes.append(merge_node)

        return merge_node.target

    def param(self, node):
        """
        Extension for parameterizing
        """
        param_parts = self.construct_scalar(node).split(' ', 1)
        if not param_parts[0] in self.params_dict:
            if len(param_parts) > 1:
                return param_parts[1].strip('"')
            else:
                return ' '
        return self.params_dict[param_parts[0]]

    def apply_inheritance(self):
        """Iterate through all YAML nodes that need to be merged"""
        for merge_node in self.merge_nodes:
            self.merge_objects(merge_node)

    def merge_lists(self, src, override):
        """For merging to YAML nodes of type list"""
        merged = []

        if src is not None and override not in self.replaced_nodes:
            for val in src:
                merged.append(val)

        for val in override:
            merged.append(val)

        return merged

    def merge_dictionaries(self, src, override):
        """For merging to YAML nodes of type dictionary"""
        merged = dict()

        if override in self.replaced_nodes:
            # Ignore source
            src = None

        if src is not None:
            # Recursively merge the children of src with children of override
            for inner_key in src:
                if inner_key in override:
                    merged_children = self.merge_objects(
                        MergeNode(src[inner_key], override[inner_key]))
                else:
                    merged_children = src[inner_key]
                if merged_children is not None:
                    merged[inner_key] = merged_children

        for inner_key in override:
            # Add the children in override that are not in src
            if src is None or inner_key not in src:
                merged[inner_key] = override[inner_key]

        return merged

    def merge_objects(self, merge_node):
        """Recursively merge two YAML nodes"""
        if merge_node.is_merged:
            return merge_node.target
        merge_node.is_merged = True

        if self.removed_node == merge_node.merge_with:
            # Indicates a YAML node being removed
            return None

        if isinstance(merge_node.starting_from,
                      MergeNode) and not merge_node.starting_from.is_merged:
            # starting_from is a merge node that needs to be processed
            merge_node.starting_from = self.merge_objects(
                merge_node.starting_from)

        if isinstance(merge_node.merge_with,
                      MergeNode) and not merge_node.merge_with.is_merged:
            # merge_with is a merge node that needs to be processed
            merge_node.merge_with = self.merge_objects(merge_node.merge_with)

        # Check for merging of two YAML lists
        if isinstance(merge_node.starting_from, list) and isinstance(
                merge_node.merge_with, list):
            merge_node.target.extend(self.merge_lists(merge_node.starting_from,
                                                      merge_node.merge_with))
            return merge_node.target

        # Check for merging of two collections
        if hasattr(merge_node.starting_from, '__iter__') and hasattr(
                merge_node.merge_with, '__iter__'):
            if isinstance(merge_node.starting_from, list) or isinstance(
                    merge_node.merge_with, list):
                # A YAML list cannot be merged with a YAML dictionary
                raise Exception("Cannot merge lists with dictionaries")

            merged = self.merge_dictionaries(merge_node.starting_from,
                                             merge_node.merge_with)
            for key in merged:
                merge_node.target[key] = merged[key]
            return merge_node.target

        else:
            # Merging scalars
            if self.removed_node == merge_node.merge_with:
                return None
            return merge_node.merge_with


YamlStratusLoader.add_constructor('!include', YamlStratusLoader.include)

YamlStratusLoader.add_constructor('!include-base64',
                                  YamlStratusLoader.include_base64)

YamlStratusLoader.add_constructor('!merge', YamlStratusLoader.merge)

YamlStratusLoader.add_constructor('!remove', YamlStratusLoader.remove)

YamlStratusLoader.add_constructor('!replace', YamlStratusLoader.replace)

YamlStratusLoader.add_constructor('!param', YamlStratusLoader.param)

YamlStratusLoader.add_constructor('!jtext', YamlStratusLoader.join_text)


class YamlStratus(object):
    """
    Class for handling YAML stratus format

    """

    def __init__(self, include_dirs=None, params=None):
        """
        Parse a YAML stratus stream returning a dictionary

        :param include_dirs: list of search paths for includes (default [])
        :param params: dictionary of parameter name-values (default {})
        """
        self.include_dirs = include_dirs
        self.params = params

    def load(self, stream):
        """
        Parse a YAML stratus stream returning a dictionary

        :param stream: stream over the YAML Stratus document
        :rtype: dictionary
        """
        loader = YamlStratusLoader(stream, include_dirs=self.include_dirs,
                                   params=self.params)
        try:
            objs = loader.get_single_data()
            loader.apply_inheritance()
            return objs
        finally:
            loader.dispose()

    def load_all(self, stream):
        """
        Stream in multiple documents in YAML Stratus format returning
        an iteration over corresponding dictionaries

        :param stream: stream over the YAML Stratus document
        :rtype: iterator over dictionaries
        """
        loader = YamlStratusLoader(stream, include_dirs=self.include_dirs,
                                   params=self.params)
        try:
            while loader.check_data():
                objs = loader.get_data()
                loader.apply_inheritance()
                yield objs
        finally:
            loader.dispose()
