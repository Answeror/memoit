#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)
        self.entries = entries

    @property
    def keys(self):
        return self.entries.keys()

    def get(self, key):
        return self.entries[key]
