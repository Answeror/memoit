#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pyquery import PyQuery as pq
#from urllib.request import urlopen
from urllib.parse import urlencode
import urllib3
from .util import Struct


BASE = 'http://dict-co.iciba.com/api/dictionary.php'


def parse(xml):
    d = pq(xml)
    word = d('key').text()
    phonetic_symbol = d('ps').eq(0).text()
    pos = d('pos').map(lambda i: pq(this).text())
    acs = d('acceptation').map(lambda i: pq(this).text())
    return Struct(
        word=word,
        phonetic_symbol=phonetic_symbol,
        custom_translations=[p + ' ' + a for p, a in zip(pos, acs)]
        )


def uri(key):
    return '%s?%s' % (BASE, urlencode({'w': key}))


#def fetch(key):
    #with urlopen(uri(key)) as f:
        #return f.read()


class Engine(object):

    def __init__(self):
        self.http = urllib3.PoolManager()

    @property
    def name(self):
        return 'iciba'

    def fetch(self, key):
        r = self.http.request('GET', uri(key))
        if r.status == 200:
            return r.data
        else:
            return None

    def query(self, key):
        try:
            data = self.fetch(key)
            if data:
                return parse(data)
        except:
            return None
