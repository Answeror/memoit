#!/usr/bin/env python
# -*- coding: utf-8 -*-


from urllib.request import urlopen
from urllib.parse import urlencode


BASE = 'http://www.iciba.com/index.php'


def uri(key):
    return '%s?%s' % (BASE, urlencode({'a': 'suggest', 's': key.replace(' ', '|1{')}))


def fetch(key):
    with urlopen(uri(key)) as f:
        return f.read()


def parse(data):
    def inner():
        for line in data.decode('utf-8').split('\n'):
            key = line.strip().split('_')[0].replace('|1{', ' ')
            if key:
                yield key
    return list(inner())


class Engine(object):

    def query(self, key):
        try:
            return parse(fetch(key))
        except:
            return None
