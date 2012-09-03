#!/usr/bin/env python
# -*- coding: utf-8 -*-

import core
from engines.util import Struct
from nose.tools import assert_equal
from textwrap import dedent


def test_format():
    d = Struct(
        word='hello',
        phonetic_symbol='''he'ləu, hə-''',
        custom_translations=[
            'n. 表示问候， 惊奇或唤起注意时的用语',
            'int. 喂；哈罗'
            ]
        )
    actual = core.format(d)
    assert_equal(actual, dedent('''\
            hello [he'ləu, hə-]
            -------------
            n. 表示问候， 惊奇或唤起注意时的用语
            int. 喂；哈罗'''))
