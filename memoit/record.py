#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: record
    :synopsis: Query record.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

import os


def empty(filepath):
    return os.stat(filepath).st_size == 0


class Recorder(object):

    def __init__(self, filepath='record'):
        self.filepath = filepath

    def add(self, word, time):
        with open(self.filepath, 'ab') as f:
            s = '{} {}'.format(word, time)
            if not empty(self.filepath):
                s = '\n' + s
            f.write(s.encode('utf-8'))
