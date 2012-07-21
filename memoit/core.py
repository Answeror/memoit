#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: pyyoudao
    :synopsis: Youdao translation.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from pyquery import PyQuery as pq
from urllib.request import urlopen
from urllib.parse import urlencode


base_url = 'http://dict.youdao.com/fsearch'


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


def query(word):
    with urlopen('%s?%s' % (base_url, urlencode({'q': word}))) as f:
        return f.read()


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


def format(s):
    sep = '-' * 13
    return '\n'.join([
        s.word if not s.phonetic_symbol else '%s [%s]' % (s.word, s.phonetic_symbol),
        sep,
        '\n'.join(s.custom_translations)
        ])


def output(s):
    print(format(s))


def main(argv):
    output(parse(query(argv[1])))
    return 0


if __name__ == '__main__':
    import sys
    main(sys.argv)
