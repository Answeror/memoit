#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtGui import QFrame, QSizePolicy
from PyQt4.QtCore import QSize


class Splitter(QFrame):

    def __init__(self, width=None, parent=None):
        super(Splitter, self).__init__(parent)
        self.setFrameStyle(QFrame.HLine)
        self.width = width
        if width:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self):
        if self.width:
            return QSize(self.width, super(Splitter, self).sizeHint().height())
        else:
            return super(Splitter, self).sizeHint()
