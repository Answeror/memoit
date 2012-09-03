#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: pyyoudao
    :synopsis: Youdao translation.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from .engines import youdao


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
    engine = youdao.Engine()
    output(engine.query(argv[1]))
    return 0


if __name__ == '__main__':
    import sys
    main(sys.argv)
