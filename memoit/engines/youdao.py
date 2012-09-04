#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: youdao
    :synopsis: Youdao translate engine.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from pyquery import PyQuery as pq
from urllib.request import urlopen
from urllib.parse import urlencode
from .util import Struct


BASE = 'http://dict.youdao.com/fsearch'


def parse(xml):
    d = pq(xml)
    word = d('return-phrase').text()
    phonetic_symbol = d('phonetic-symbol').text()
    contents = d('custom-translation > translation > content')
    trans = contents.map(lambda i: pq(this).text())
    return Struct(
        word=word,
        phonetic_symbol=phonetic_symbol,
        custom_translations=[t for t in trans if not t is None]
        )


def uri(key):
    return '%s?%s' % (BASE, urlencode({'q': key}))


def fetch(key):
    with urlopen(uri(key)) as f:
        return f.read()


class Engine(object):

    @property
    def name(self):
        return 'youdao'

    def query(self, key):
        try:
            return parse(fetch(key))
        except:
            return None
