#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: anki
    :synopsis: Anki related.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from urllib.request import HTTPCookieProcessor, build_opener
from urllib.parse import urlencode
from pyquery import PyQuery as pq


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
        if params:
            opener.open(url + '?' + urlencode(params))
        else:
            opener.open(url)
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


def remove(opener, front):
    with urlopen(opener, 'http://ankiweb.net/deck/list', {'keyword': front}) as f:
        d = pq(f.read().decode('utf-8'))
    tr = d('tr').filter(lambda i: pq(this)('td').eq(1).text() == front)
    href = next(iter(tr.map(lambda i: pq(this)('td').eq(0)('a').eq(1).attr('href'))), None)
    if href:
        return post(opener, 'http://ankiweb.net' + href, {})
    return True


def add(opener, front, back):
    return remove(opener, front) and post(
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
