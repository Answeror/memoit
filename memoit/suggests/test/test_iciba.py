#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .. import iciba
import os
from nose.tools import assert_equal
from mock import patch, sentinel


ROOT = os.path.dirname(__file__)


def frame_keys_iciba():
    with open(os.path.join(ROOT, 'frame_keys.iciba.txt'), 'r') as f:
        return [word.strip() for word in f if word.strip()]


def frame_iciba():
    with open(os.path.join(ROOT, 'frame.iciba.txt'), 'rb') as f:
        return f.read()


@patch.object(iciba, 'parse')
@patch.object(iciba, 'fetch')
def test_engine(fetch, parse):
    fetch.return_value = sentinel.response
    parse.return_value = sentinel.result
    engine = iciba.Engine()
    assert_equal(engine.query(sentinel.key), sentinel.result)
    fetch.assert_called_with(sentinel.key)
    parse.assert_called_with(sentinel.response)


@patch.object(iciba, 'urlopen')
@patch.object(iciba, 'uri')
def test_fetch(uri, urlopen):
    uri.return_value = sentinel.uri
    urlopen.return_value.__enter__.return_value.read.return_value = sentinel.response
    assert_equal(iciba.fetch(sentinel.key), sentinel.response)
    uri.assert_called_with(sentinel.key)
    urlopen.assert_called_with(sentinel.uri)


def test_uri():
    assert_equal(iciba.uri('frame'), 'http://www.iciba.com/index.php?a=suggest&s=frame')


def test_spaced_key_uri():
    assert_equal(iciba.uri('frame work'), 'http://www.iciba.com/index.php?a=suggest&s=frame%7C1%7Bwork')


def test_parse():
    assert_equal(iciba.parse(frame_iciba()), frame_keys_iciba())
