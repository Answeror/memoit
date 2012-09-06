#!/usr/bin/env python
# -*- coding: utf-8 -*-


from .signal import SignalObject


from PyQt4.QtCore import\
        QRunnable,\
        QMutex,\
        QMutexLocker


class Runnable(QRunnable):
    """Wrap ``fn`` in a mutex and emit signal using the return value of
    ``fn``."""

    mutex = QMutex()

    def __init__(self, fn, args=(bool,)):
        super(Runnable, self).__init__()
        self.fn = fn
        self.finished = SignalObject(*args)

    def run(self):
        with QMutexLocker(self.mutex):
            self.finished.emit(self.fn())
