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


def getter_name(key):
    return key


def setter_name(key):
    return 'set_' + key


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
    for e in iterable:
        pass


def settings(items, *args, **kargs):
    """Construct a settings object.

    ``args`` and ``kargs`` are used as ``QSettings`` parameters,
    see `http://qt-project.org/doc/qt-4.8/qsettings.html`_ for details.

    >>> from PyQt4.QtCore import QSettings
    >>> from tempfile import NamedTemporaryFile as ntf
    >>> f = ntf(suffix='.ini', delete=False)
    >>> s = settings(dict(name='foo', age=42), f.name, QSettings.IniFormat)
    >>> print(s.name, s.age)
    foo 42
    >>> s.name, s.age = 'bar', 13
    >>> print(s.name, s.age)
    bar 13

    >>> from PyQt4.QtCore import QObject, pyqtSlot
    >>> class Observer(QObject):
    ...     @pyqtSlot(str)
    ...     def react(self, value):
    ...         print('new name ' + value)
    >>> class Trigger(QObject):
    ...     send = pyqtSignal(str)
    >>> f = ntf(suffix='.ini', delete=False)
    >>> s = settings(dict(name='foo'), f.name, QSettings.IniFormat)
    >>> t = Trigger()
    >>> t.send.connect(s.set_name)
    >>> o = Observer()
    >>> s.name_changed.connect(o.react)
    >>> t.send.emit('bar')
    new name bar

    :param items: keys and their default values
    :type items: dict of (str, any type)
    :return: settings object
    """
    class Settings(QObject):

        def __init__(self):
            super(Settings, self).__init__()
            self.settings = QSettings(*args, **kargs)

    def deal(key, default):
        def get(self):
            return self.settings.value(key, default)

        get.__name__ = getter_name(key)

        def set(self, value):
            if getattr(self, key) == value:
                return
            self.settings.setValue(key, value)
            getattr(self, signal_name(key)).emit(value)

        set.__name__ = setter_name(key)

        setattr(Settings, key, pyqtProperty(type(default), get, set))
        # cannot directly use pyqtSignal here, cause python crash
        setattr(Settings, signal_name(key), signal(type(default)))
        setattr(Settings, setter_name(key), set)
        setattr(Settings, setter_name(key), getattr(Settings, setter_name(key)))

    eat(starmap(deal, items.items()))

    return Settings()
