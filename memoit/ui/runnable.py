#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtCore import QRunnable, QThreadPool
from .signal import Signal


class Runnable(QRunnable):
    """Wrap ``fn`` in a mutex and emit signal using the return value of
    ``fn``."""

    def __init__(self, fn, args=(bool,)):
        super(Runnable, self).__init__()
        self.fn = fn
        self.finished = Signal(*args)
        self.isaction = not bool(args)

    def run(self):
        if self.isaction:
            self.fn()
            self.finished.emit()
        else:
            self.finished.emit(self.fn())


def async_actions(actions):
    start = QThreadPool.globalInstance().start
    list(map(lambda a: start(Runnable(a, args=())), actions))
