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
        QDialog,\
        QGroupBox
from PyQt4.QtCore import\
        QRunnable,\
        Qt,\
        QObject,\
        pyqtSignal,\
        QMutex,\
        QFile,\
        QEvent,\
        QTimer,\
        QMutexLocker, QThreadPool, pyqtSlot
from .anki import Recorder
from datetime import datetime
from . import resources_rc
#import os
from .settings import settings

from .core import format
from .engines import youdao, iciba


class Input(QLineEdit):

    def __init__(self, changed):
        super(Input, self).__init__()
        self.changed = changed

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
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


class Group(QGroupBox):

    def __init__(self, engine):
        super(Group, self).__init__(engine.name)
        layout = QVBoxLayout()
        layout.addWidget(Output(engine))
        self.setLayout(layout)


class Engine(QObject):

    query_start = pyqtSignal()
    query_finished = pyqtSignal(object)

    @property
    def name(self):
        return self.impl.name

    def __init__(self, impl):
        super(Engine, self).__init__()
        self.impl = impl

    def query(self, key):
        self.query_start.emit()
        runnable = Runnable(lambda: self.impl.query(key), args=(object,))
        runnable.finished.connect(self.query_finished)
        QThreadPool.globalInstance().start(runnable)


def SignalObject(*args):
    class Inner(QObject):
        """Provide signal functionality to QRunnable."""

        sig = pyqtSignal(*args)

        def emit(self, *args):
            self.sig.emit(*args)

        def connect(self, *args):
            self.sig.connect(*args)

    return Inner()


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
        self.engines[0].query_finished.connect(self.record)

        def query(key):
            for engine in self.engines:
                engine.query(key)

        layout = QVBoxLayout()
        input_edit = Input(query)
        layout.addWidget(input_edit)
        for engine in self.engines:
            layout.addWidget(Group(engine))
        self.setLayout(layout)

        # tray
        self.tray = Tray(QIcon(':/tray.png'), self)
        self.tray.activated.connect(self.icon_activated)
        self.tray.show()

        # must after settings set up
        self.try_login()

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
                self.recorder = Recorder(
                    username=self.settings.username,
                    password=self.settings.password,
                    deck=self.settings.deck
                    )
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
    def record(self, s):
        """Record in background."""
        if not self.recorder is None:
            runnable = Runnable(lambda: self.recorder.add(
                    word=s.word,
                    pron=s.phonetic_symbol,
                    trans='\n'.join(s.custom_translations),
                    time=datetime.now()
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
    win = Window()
    win.show()
    return app.exec_()


if __name__ == '__main__':
    import sys
    main(sys.argv)
