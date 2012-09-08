#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: anki
    :synopsis: Anki related.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from urllib.request import HTTPCookieProcessor, build_opener
from urllib.parse import urlencode


def urlopen(opener, url, params):
    return opener.open(url + '?' + urlencode(params))


def make_opener(username, password):
    try:
        cookies = HTTPCookieProcessor()
        opener = build_opener(cookies)
        with urlopen(
            opener,
            'http://ankiweb.net/account/login',
            {'username': username, 'password': password}
            ) as f:
            if not f.geturl().startswith('http://ankiweb.net/study'):
                return None
        return opener
    except:
        return None


def post(opener, url, params):
    try:
        opener.open(url + '?' + urlencode(params))
    except:
        return False
    else:
        return True


def activate(opener, deck):
    return post(
        opener,
        'http://ankiweb.net/deck/manage',
        {'cmd': 'setActive', 'deck': deck}
        )


def add(opener, front, back):
    return post(
        opener,
        'http://ankiweb.net/deck/edit',
        {'Front': front, 'Back': back, 'action': 'Add'}
        )


class Recorder(object):
    """Thread safe Anki recorder."""

    def __init__(self, username, password, deck):
        self.opener = make_opener(username, password)
        if self.opener is None:
            raise RuntimeError('Login failed.')
        if not activate(self.opener, deck):
            raise RuntimeError('Open deck failed.')

    #def add(self, word, trans, pron=None, **kargs):
    def add(self, key, responses):
        p = next(filter(lambda r: hasattr(r, 'phonetic_symbol'), responses), None)
        return add(
            self.opener,
            front=key if not p else '%s [%s]' % (key, p.phonetic_symbol),
            back='\n\n'.join([str(r) for r in responses])
            )
