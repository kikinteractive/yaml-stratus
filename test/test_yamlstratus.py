#!/usr/bin/env python
"""
Tests for yamlstratus
"""
import json
import os
import os.path
import yamlstratus

test_dir = 'test'


def compare_json(expected, actual):
    """
    Compares to dictionaries representing json objects
    :param expected: The expected json
    :param actual: The actual json
    :return: where the two json representations are equal
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            assert actual == expected
        assert isinstance(actual, dict)
        assert len(expected) == len(actual)
        for expected_key in expected:
            assert expected_key in actual
            compare_json(expected[expected_key], actual[expected_key])
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        assert len(expected) == len(actual)
        cnt = 0
        while cnt < len(expected):
            compare_json(expected[cnt], actual[cnt])
            cnt += 1
    else:
        assert expected == actual


def get_test_pairs(dir):
    """
    Pulls out pairs of files corresponding to a test yaml file and ab
    expected json file
    :param dir: the directory in which to search for such pairs
    :return: iterator over test pairs
    """
    for filename in os.listdir(dir):
        if not filename.endswith('.json'):
            continue
        # .yaml named same as corresponding .json
        yield (os.path.join(test_dir, filename),
               os.path.join(test_dir, filename[:-5] + '.yaml'))


def test_load_all():
    """Tests yamlstratus.load_all()"""
    for json_filename, yaml_filename in get_test_pairs(test_dir):
        with open(json_filename, 'r') as json_f:
            all_expected_json = json.loads(json_f.read())
        with open(yaml_filename, 'r') as yaml_f:
            json_cnt = 1
            for actual_json in yamlstratus.load_all(
                    yaml_f,
                    **all_expected_json[0]):
                expected_json = all_expected_json[json_cnt]
                compare_json(expected_json, actual_json)
                json_cnt += 1


def test_load_all_as_json():
    """Tests yamlstratus.load_all_as_json()"""
    for json_filename, yaml_filename in get_test_pairs(test_dir):
        with open(json_filename, 'r') as json_f:
            all_expected_json = json.loads(json_f.read())
        with open(yaml_filename, 'r') as yaml_f:
            json_cnt = 1
            for actual_json_str in yamlstratus.load_all_as_json(
                    yaml_f,
                    **all_expected_json[0]):
                actual_json = json.loads(actual_json_str)
                expected_json = all_expected_json[json_cnt]
                compare_json(expected_json, actual_json)
                json_cnt += 1


def test_to_json():
    """Tests yamlstratus.load_all()"""
    for json_filename, yaml_filename in get_test_pairs(test_dir):
        with open(json_filename, 'r') as json_f:
            all_expected_json = json.loads(json_f.read())
        with open(yaml_filename, 'r') as yaml_f:
            json_cnt = 1
            for actual_json in yamlstratus.load_all(
                    yaml_f,
                    **all_expected_json[0]):
                actual_json_str = yamlstratus.to_json(actual_json)
                actual_json = json.loads(actual_json_str)
                expected_json = all_expected_json[json_cnt]
                compare_json(expected_json, actual_json)
                json_cnt += 1


def test_load():
    """Tests yamlstratus.load()"""
    for json_filename, yaml_filename in get_test_pairs(test_dir):
        with open(json_filename, 'r') as json_f:
            all_expected_json = json.loads(json_f.read())
        with open(yaml_filename, 'r') as yaml_f:
            json_cnt = 1
            # Split yaml file into parts, testing each individually
            for yaml in yaml_f.read().split('---')[1:]:
                actual_json = yamlstratus.load(yaml, **all_expected_json[0])
                expected_json = all_expected_json[json_cnt]
                compare_json(expected_json, actual_json)
                json_cnt += 1


def test_load_as_json():
    """Tests yamlstratus.load_as_json()"""
    for json_filename, yaml_filename in get_test_pairs(test_dir):
        with open(json_filename, 'r') as json_f:
            all_expected_json = json.loads(json_f.read())
        with open(yaml_filename, 'r') as yaml_f:
            json_cnt = 1
            # Split yaml file into parts, testing each individually
            for yaml in yaml_f.read().split('---')[1:]:
                actual_json_str = yamlstratus.load_as_json(
                    yaml,
                    **all_expected_json[0])
                actual_json = json.loads(actual_json_str)
                expected_json = all_expected_json[json_cnt]
                compare_json(expected_json, actual_json)
                json_cnt += 1


def test_include_file_not_found():
    yaml_str = """
                ---
                # Include root node of invalid file
                main: !include unknown
                ---
                # Include invalid file
                main:
                    top: !include unknown
                """
    for yaml in yaml_str.split('---')[1:]:
        try:
            yamlstratus.load_as_json(yaml, include_dirs=["test"])
            assert False
        except IOError:
            pass

def test_include_error():
    yaml_str = """
                ---
                # Include down one to unknown tag
                main:
                    top: !include test1.unknown
                ---
                # Include down many levels to unknown tag
                main:
                top: !include test1.level1.level2.level3.level4.unknown
                """
    for yaml in yaml_str.split('---')[1:]:
        try:
            yamlstratus.load_as_json(yaml, include_dirs=["test"])
            assert False
        except KeyError:
            pass

def test_include_base64_file_not_found():
    yaml_str = """
                ---
                # Include
                main: !include-base64 unknown.yaml
                ---
                # Include where suffix understood
                main: !include-base64 unknown
                """
    for yaml in yaml_str.split('---')[1:]:
        try:
            yamlstratus.load_as_json(yaml, include_dirs=["test"])
            assert False
        except IOError:
            pass

def test_merge_syntax_errors():
    yaml_str = """
                ---
                main:
                    top: !merge
                        startingFrom:
                            - value1
                            - value2
                ---
                main:
                    top: !merge
                        mergeWith:
                            - value1
                            - value2
                ---
                main:
                    top: !merge
                        startingWith:
                            - value1
                            - value2
                        mergeFrom:
                            - value1
                            - value2
                ---
                main:
                    top: !merge
                        startingFrom:
                            - value1
                            - value2
                        mergeWith:
                            - value1
                            - value2
                        extraNode:
                            - value1
                            - value2
                """
    for yaml in yaml_str.split('---')[1:]:
        try:
            yamlstratus.load_as_json(yaml, include_dirs=["test"])
            assert False
        except KeyError:
            pass

def test_merge_type_mismatch_errors():
    yaml_str = """
                ---
                main:
                    top: !merge
                        startingFrom:
                            - value1
                        mergeWith:
                            key1: value1
                ---
                main:
                    top: !merge
                        startingFrom:
                            key1: value1
                        mergeWith:
                            - value1
                ---
                main:
                    top: !merge
                        startingFrom:
                            key1: value
                        mergeWith: 123
                ---
                main:
                    top: !merge
                        startingFrom: 123
                        mergeWith:
                            key1: value
                ---
                main:
                    top: !merge
                        startingFrom:
                            - value1
                        mergeWith: 123
                ---
                main:
                    top: !merge
                        startingFrom: 123
                        mergeWith:
                            - value1
                ---
                main:
                    top: !merge
                        startingFrom: 123
                        mergeWith: 123
                ---
                main:
                    top: !merge
                        startingFrom: value1
                        mergeWith: value2
                """
    for yaml in yaml_str.split('---')[1:]:
        try:
            yamlstratus.load_as_json(yaml, include_dirs=["test"])
            assert False
        except ValueError:
            pass
