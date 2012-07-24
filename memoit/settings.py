#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: settings
    :synopsis: Provide Settings class.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from PyQt4.QtCore import QObject, QSettings, pyqtProperty, pyqtSignal
from itertools import starmap


def signal_name(key):
    return key + '_changed'


def signal(type):
    """Object act like a pyqtSignal."""
    class Signal(QObject):

        signal = pyqtSignal(type)

        def emit(self, value):
            return self.signal.emit(value)

        def connect(self, slot):
            return self.signal.connect(slot)

    return Signal()


def eat(iterable):
    """Eat iterable elements."""
    for e in iterable: pass


def settings(items, organization=None, application=None):
    """Construct a settings object.

    :param items: keys and their default values
    :type items: dict of (str, any type)
    :return: settings object
    """
    class Settings(QObject):

        def __init__(self):
            super(Settings, self).__init__()
            if not organization is None and not application is None:
                self.settings = QSettings(organization, application)
            else:
                self.settings = QSettings()

    def deal(key, default):
        def get(self):
            return self.settings.value(key, default)

        def set(self, value):
            if getattr(self, key) == value:
                return
            self.settings.setValue(key, value)
            getattr(self, signal_name(key)).emit(value)

        setattr(Settings, key, pyqtProperty(type(default), get, set))
        # cannot directly use pyqtSignal here, cause python crash
        setattr(Settings, signal_name(key), signal(type(default)))

    eat(starmap(deal, items.items()))

    return Settings()
