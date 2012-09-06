#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .. import iciba
import os
from nose.tools import assert_true, assert_equal
from mock import sentinel, patch


ROOT = os.path.dirname(__file__)


def hello():
    with open(os.path.join(ROOT, 'hello.iciba.xml'), 'rb') as f:
        return f.read()

def test_parse():
    ret = iciba.parse(hello())
    for key, value in [
            ('word', 'hello'),
            ('phonetic_symbol', '''heˈləu'''),
            ('custom_translations', [
                'int. 哈喽，喂；你好，您好；表示问候；打招呼；',
                'n. “喂”的招呼声或问候声；',
                'vi. 喊“喂”；'
                ])
            ]:
        assert_true(key in ret.keys)
        assert_equal(value, ret.get(key))


#@patch.object(iciba, 'parse')
#@patch.object(iciba, 'urlopen')
#def test_engine(urlopen, parse):
    #urlopen.return_value.__enter__.return_value.read.return_value = sentinel.hello
    #engine = iciba.Engine()
    #engine.query('hello')
    #parse.assert_called_with(sentinel.hello)


def test_uri():
    assert_equal(iciba.uri('hello'),
            'http://dict-co.iciba.com/api/dictionary.php?w=hello')
