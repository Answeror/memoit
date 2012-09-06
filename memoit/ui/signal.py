#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtCore import QObject, pyqtSignal


def SignalObject(*args):
    class Inner(QObject):
        """Provide signal functionality to QRunnable."""

        sig = pyqtSignal(*args)

        def emit(self, *args):
            self.sig.emit(*args)

        def connect(self, *args):
            self.sig.connect(*args)

    return Inner()
