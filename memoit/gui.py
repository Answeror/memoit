#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: gui
    :synopsis: Qt version.

.. moduleauthor:: Answeror <answeror@gmail.com>

"""

from PyQt4.QtGui import\
        QLabel,\
        QLineEdit,\
        QWidget,\
        QMessageBox,\
        QTextEdit,\
        QVBoxLayout,\
        QHBoxLayout,\
        QFont,\
        QSystemTrayIcon,\
        QMenu,\
        QApplication,\
        QIcon,\
        QPushButton,\
        QGridLayout,\
        QDialog
from PyQt4.QtCore import\
        Qt,\
        QObject,\
        pyqtSignal,\
        pyqtSlot,\
        pyqtProperty,\
        QFile,\
        QEvent,\
        QTimer,\
        QThreadPool,\
        QRunnable,\
        QMutex,\
        QMutexLocker,\
        QSemaphore
from functools import partial
from queue import Queue
from .anki import Recorder
#from datetime import datetime
from . import resources_rc
#import os
from .settings import settings
from .ui.runnable import Runnable, async_actions
from .ui.suggest import Suggest
from .ui.splitter import Splitter

from .core import format
from .engines import youdao, iciba


STYLESHEET = 'style.css'


class Title(QWidget):
    """Translation area title widget."""

    def __init__(self, name, parent=None):
        super(Title, self).__init__(parent)
        layout = QHBoxLayout()
        self.toggler = Toggler(text=name, checked=False)
        layout.addWidget(Splitter())
        layout.addWidget(self.toggler)
        layout.addWidget(Splitter())
        self.setLayout(layout)


class Toggler(QPushButton):

    def __init__(self, text, checked, parent=None):
        super(Toggler, self).__init__(text, parent=parent)
        self.setCheckable(True)
        self.setChecked(checked)


class Input(QLineEdit):

    def __init__(self, changed):
        super(Input, self).__init__()
        self.changed = changed
        self.completer = Suggest(self)
        self.last_key = None

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.last_key = self.text()
            self.changed(self.text())
        elif e.key() == Qt.Key_Escape:
            self.setText('')
        super(Input, self).keyPressEvent(e)


class Output(QTextEdit):

    def __init__(self, engine):
        super(Output, self).__init__()
        self.setReadOnly(True)
        self.setFont(QFont('Lucida Sans Unicode'))

        self.engine = engine
        self.engine.query_start.connect(self.invalidate)
        self.engine.query_finished.connect(self.react)

    @pyqtSlot()
    def invalidate(self):
        self.setText('Loading...')

    @pyqtSlot(object)
    def react(self, result):
        if result is None:
            self.setText('')
        else:
            self.setText(format(result))


class Group(QWidget):
    """Translation area."""

    # name checking state changed
    toggled = pyqtSignal(bool)

    def __init__(self, engine, parent=None):
        super(Group, self).__init__(parent)
        self.engine = engine
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.title = Title(engine.name)
        self.title.toggler.toggled.connect(self.toggled)
        layout.addWidget(self.title)
        layout.addWidget(Output(engine))
        self.setLayout(layout)

    def selected(self):
        return self.title.toggler.isChecked()

    def last_result(self):
        return self.engine.last_result


class Engine(QObject):

    query_start = pyqtSignal()
    query_finished = pyqtSignal(object)

    @pyqtProperty(str)
    def name(self):
        return self.impl.name

    def __init__(self, impl):
        super(Engine, self).__init__()
        self.impl = impl
        self.mutex = QMutex()

    def query(self, key):
        with QMutexLocker(self.mutex):
            self.query_start.emit()
            self._query_finished(self.impl.query(key))

    def _query_finished(self, result):
        """Save last result and emit finished signal."""
        self.last_result = result
        self.query_finished.emit(result)


class SettingsDialog(QDialog):

    def __init__(self, settings, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.settings = settings

        self.setWindowTitle('Settings')
        layout = QVBoxLayout()

        settings_layout = QGridLayout()
        username_label = QLabel('Username:')
        settings_layout.addWidget(username_label, 0, 0)
        self.username_edit = QLineEdit()
        settings_layout.addWidget(self.username_edit, 0, 1)
        password_label = QLabel('Password:')
        settings_layout.addWidget(password_label, 1, 0)
        self.password_edit = QLineEdit()
        settings_layout.addWidget(self.password_edit, 1, 1)
        deck_label = QLabel('Deck:')
        settings_layout.addWidget(deck_label, 2, 0)
        self.deck_edit = QLineEdit()
        settings_layout.addWidget(self.deck_edit, 2, 1)
        layout.addLayout(settings_layout)

        button_layout = QHBoxLayout()
        accept_button = QPushButton('&Accept')
        accept_button.clicked.connect(self.accept)
        button_layout.addWidget(accept_button)
        reject_button = QPushButton('&Cancel')
        reject_button.clicked.connect(self.reject)
        button_layout.addWidget(reject_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def showEvent(self, e):
        self.username_edit.setText(self.settings.username)
        self.password_edit.setText(self.settings.password)
        self.deck_edit.setText(self.settings.deck)
        super(SettingsDialog, self).showEvent(e)

    def accept(self):
        self.settings.username = self.username_edit.text()
        self.settings.password = self.password_edit.text()
        self.settings.deck = self.deck_edit.text()
        return super(SettingsDialog, self).accept()


class Tray(QSystemTrayIcon):

    def __init__(self, icon, parent):
        super(Tray, self).__init__(icon, parent)
        menu = QMenu()
        menu.addAction('&Settings').triggered.connect(parent.settings_dialog.exec_)
        menu.addAction('&About').triggered.connect(parent.about)
        menu.addAction('&Exit').triggered.connect(QApplication.instance().quit)
        self.setContextMenu(menu)


def dump_queue(queue):
    """Empties all pending items in a queue and returns them in a list."""
    result = []
    queue.put('STOP')
    for i in iter(queue.get, 'STOP'):
        result.append(i)
    return result


class Collect(QRunnable):
    """Collect results from engines and emit signal."""

    def __init__(self, engines, finished):
        super(Collect, self).__init__()
        self.engines = engines
        self.semaphore = QSemaphore()
        self.queue = Queue()
        self.finished = finished
        for engine in engines:
            engine.query_finished.connect(self.handle_query_finished)

    def run(self):
        for i in range(len(self.engines)):
            self.semaphore.acquire()
        self.finished(dump_queue(self.queue))

    @pyqtSlot(object)
    def handle_query_finished(self, response):
        self.queue.put(response)
        self.semaphore.release()


class ThreadSafeRecorder(QObject):

    def __init__(self, impl):
        QObject.__init__(self)
        self.impl = impl
        self.mutex = QMutex()

    def add(self, key, responses):
        with QMutexLocker(self.mutex):
            return self.impl.add(key=key, responses=responses)


class Window(QWidget):

    def __init__(self):
        super(Window, self).__init__()

        self.recorder = None

        # settins
        self.settings = settings(dict(
            username='',
            password='',
            deck=''
            ))
        self.settings_dialog = SettingsDialog(self.settings)
        self.settings_dialog.accepted.connect(self.login)

        # main window
        self.setWindowTitle('memoit')

        self.engines = [Engine(youdao.Engine()), Engine(iciba.Engine())]

        layout = QVBoxLayout()
        self.input_area = Input(self.query)
        layout.addWidget(self.input_area)
        self.output_areas = []
        for engine in self.engines:
            area = Group(engine)
            area.toggled.connect(self.handle_area_toggled)
            layout.addWidget(area)
            self.output_areas.append(area)
        self.setLayout(layout)

        # tray
        self.tray = Tray(QIcon(':/tray.png'), self)
        self.tray.activated.connect(self.icon_activated)
        self.tray.show()

        # must after settings set up
        self.try_login()

        # let the whole window be a glass
        try:
            self.setAttribute(Qt.WA_NoSystemBackground)
            from ctypes import windll, c_int, byref
            windll.dwmapi.DwmExtendFrameIntoClientArea(
                    c_int(self.winId()), byref(c_int(-1)))
        except:
            pass

    @pyqtSlot(bool)
    def handle_area_toggled(self, selected):
        if self.input_area.last_key:
            self.record(
                self.input_area.last_key,
                list(map(Group.last_result, filter(Group.selected, self.output_areas)))
                )

    def query(self, key):
        """Emit query."""
        collect = Collect(
            list(map(lambda a: a.engine, filter(Group.selected, self.output_areas))),
            lambda r: self.record(key, r)
            )
        QThreadPool.globalInstance().start(collect)
        #for engine in self.engines:
            #QThreadPool.globalInstance().start(
                    #Runnable(lambda: engine.query(key), args=(object,)))
        async_actions(map(lambda e: partial(e.query, key), self.engines))

    def closeEvent(self, e):
        QApplication.instance().quit()
        super(Window, self).closeEvent(e)

    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide)
        else:
            super(Window, self).changeEvent(e)

    @pyqtSlot(Tray.ActivationReason)
    def icon_activated(self, reason):
        if reason == Tray.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                # work but lose old window position
                # see `http://qt-project.org/forums/viewreply/36525/`_
                #flags = self.windowFlags()
                #flags |= Qt.WindowStaysOnTopHint
                #self.setWindowFlags(flags)
                #flags &= ~Qt.WindowStaysOnTopHint
                #self.setWindowFlags(flags)
                #self.showNormal()

                # perfect
                # see `http://stackoverflow.com/a/7820461`_
                # ``Qt.WindowNoState`` and ``Qt.WindowActive`` are all
                # acceptable
                # ``show`` and ``setWindowState`` calling order matters
                # if ``show`` first and window is minimized (not close)
                # then this call order will produce "fly in" effect
                # but for bdist version, ``setWindowState`` first wiil
                # cause focus lost
                self.setWindowState(Qt.WindowActive)
                self.show()
                self.raise_()
                self.activateWindow()

    @pyqtSlot()
    def about(self):
        f = QFile(':/about.txt')
        if not f.open(QFile.ReadOnly | QFile.Text):
            assert False, f.errorString()
        QMessageBox.about(self, 'About', bytes(f.readAll()).decode('utf-8'))

    def try_login(self):
        if self.settings.username:
            self.login()

    def login(self):
        assert self.settings.username,\
            'Invalid username: %s' % self.settings.username

        def inner():
            try:
                self.recorder = ThreadSafeRecorder(Recorder(
                    username=self.settings.username,
                    password=self.settings.password,
                    deck=self.settings.deck
                    ))
            except:
                return False
            else:
                return True

        runnable = Runnable(inner)
        runnable.finished.connect(self.logined)
        QThreadPool.globalInstance().start(runnable)

    @pyqtSlot(bool)
    def logined(self, success):
        if not success:
            QMessageBox.warning(self, 'Anki', 'Login failed.')
        else:
            self.tray.showMessage('Anki', 'Login succeed.')

    @pyqtSlot(object)
    def record(self, key, responses):
        """Record in background."""
        if not self.recorder is None:
            runnable = Runnable(lambda: self.recorder.add(
                    #word=s.word,
                    #pron=s.phonetic_symbol,
                    #trans='\n'.join(s.custom_translations),
                    #time=datetime.now()
                    key=key,
                    responses=responses
                    ))
            runnable.finished.connect(self.recorded)
            QThreadPool.globalInstance().start(runnable)

    @pyqtSlot(bool)
    def recorded(self, success):
        if not success:
            QMessageBox.warning(self, 'Anki', 'Record failed.')


def main(argv):
    app = QApplication(argv)
    app.setOrganizationName('helanic')
    app.setOrganizationDomain('answeror.com')
    app.setApplicationName('memoit')
    # do not quit when main window in hidden and tray menu generated dialog
    # closed
    # see `http://stackoverflow.com/a/7979775/238472`_ for details
    app.setQuitOnLastWindowClosed(False)
    # don't know why
    app.setWindowIcon(QIcon(':/taskbar.png'))
    # style
    with open(STYLESHEET, 'r') as f:
        app.setStyleSheet(f.read())
    win = Window()
    win.show()
    return app.exec_()


if __name__ == '__main__':
    import sys
    main(sys.argv)
