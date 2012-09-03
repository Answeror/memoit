#!/usr/bin/env python
# -*- coding: utf-8 -*-

# don't use relative import here, for mock doesn't support it
# from .. import youdao
import youdao
import os
from nose.tools import assert_true, assert_equal
from mock import sentinel, patch


ROOT = os.path.dirname(__file__)


def hello():
    with open(os.path.join(ROOT, 'hello.xml'), 'rb') as f:
        return f.read()

def test_parse():
    ret = youdao.parse(hello())
    for key, value in [
            ('word', 'hello'),
            ('phonetic_symbol', '''he'ləu, hə-'''),
            ('custom_translations', [
                'n. 表示问候， 惊奇或唤起注意时的用语',
                'int. 喂；哈罗'
                ])
            ]:
        assert_true(key in ret.keys)
        assert_equal(value, ret.get(key))


@patch('youdao.parse')
@patch('youdao.urlopen')
def test_engine(urlopen, parse):
    urlopen.return_value.__enter__.return_value.read.return_value = sentinel.hello
    engine = youdao.Engine()
    engine.query('hello')
    parse.assert_called_with(sentinel.hello)


def test_uri():
    assert_equal(youdao.uri('hello'), 'http://dict.youdao.com/fsearch?q=hello')
