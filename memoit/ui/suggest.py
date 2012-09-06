#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtGui import\
        QTreeWidget,\
        QFrame,\
        QTreeWidgetItem
from PyQt4.QtCore import\
        Qt,\
        QPoint,\
        QObject,\
        pyqtSignal,\
        pyqtSlot,\
        QEvent,\
        QTimer,\
        QThreadPool,\
        QMetaObject
from ..suggests import iciba
from .runnable import Runnable


class Engine(QObject):

    query_start = pyqtSignal()
    query_finished = pyqtSignal(object)

    def __init__(self, impl):
        super(Engine, self).__init__()
        self.impl = impl

    def query(self, key):
        self.query_start.emit()
        runnable = Runnable(lambda: self.impl.query(key), args=(object,))
        runnable.finished.connect(self.query_finished)
        QThreadPool.globalInstance().start(runnable)


class Suggest(QObject):

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.editor = parent
        editor = self.editor

        self.popup = QTreeWidget()
        popup = self.popup
        popup.setWindowFlags(Qt.Popup)
        popup.setFocusPolicy(Qt.NoFocus)
        popup.setFocusProxy(parent)
        popup.setMouseTracking(True)

        popup.setColumnCount(1)
        popup.setUniformRowHeights(True)
        popup.setRootIsDecorated(False)
        popup.setEditTriggers(QTreeWidget.NoEditTriggers)
        popup.setSelectionBehavior(QTreeWidget.SelectRows)
        popup.setFrameStyle(QFrame.Box | QFrame.Plain)
        popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        popup.header().hide()

        popup.installEventFilter(self)

        popup.itemClicked.connect(self.done)

        self.timer = QTimer(self)
        timer = self.timer
        timer.setSingleShot(True)
        # TODO: make interval optional
        timer.setInterval(500)
        timer.timeout.connect(self.suggest)
        editor.textEdited.connect(timer.start)

        self.engine = Engine(iciba.Engine())
        self.engine.query_finished.connect(self.handle_query_finished)

    def eventFilter(self, o, e):
        if not o is self.popup:
            return False

        if e.type() == QEvent.MouseButtonPress:
            self.popup.hide()
            self.editor.setFocus()
            return True

        if e.type() == QEvent.KeyPress:
            consumed = False
            key = e.key()
            if key in (Qt.Key_Enter, Qt.Key_Return):
                self.done()
                consumed = True
            elif key in (Qt.Key_Escape, ):
                self.editor.setFocus()
                self.popup.hide()
                consumed = True
            elif key in (
                    Qt.Key_Up,
                    Qt.Key_Down,
                    Qt.Key_Home,
                    Qt.Key_End,
                    Qt.Key_PageUp,
                    Qt.Key_PageDown
                    ):
                pass
            else:
                self.editor.setFocus()
                self.editor.event(e)
                self.popup.hide()
            return consumed

        return False

    def complete(self, choices):
        if not choices:
            return

        self.popup.setUpdatesEnabled(False)
        self.popup.clear()
        for i in range(len(choices)):
            item = QTreeWidgetItem(self.popup)
            item.setText(0, choices[i])
        self.popup.setCurrentItem(self.popup.topLevelItem(0))
        self.popup.resizeColumnToContents(0)
        self.popup.resizeColumnToContents(1)
        self.popup.adjustSize()
        self.popup.setUpdatesEnabled(True)

        h = self.popup.sizeHintForRow(0) * min(7, len(choices)) + 3
        self.popup.resize(self.popup.width(), h)

        self.popup.move(self.editor.mapToGlobal(QPoint(0, self.editor.height())))
        self.popup.setFocus()
        self.popup.show()

    @pyqtSlot()
    def done(self):
        self.timer.stop()
        self.popup.hide()
        self.editor.setFocus()
        item = self.popup.currentItem()
        if item:
            self.editor.setText(item.text(0))
            QMetaObject.invokeMethod(self.editor, "returnPressed")

    @pyqtSlot()
    def suggest(self):
        key = self.editor.text()
        self.engine.query(key)

    @pyqtSlot()
    def stop(self):
        self.timer.stop()

    @pyqtSlot(object)
    def handle_query_finished(self, result):
        self.complete(result)
