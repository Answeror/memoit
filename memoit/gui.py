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
from PyQt4.QtCore import QRunnable, Qt, QObject, pyqtSignal, QMutex,\
        QSettings,\
        QFile,\
        QMutexLocker, QThreadPool, pyqtSlot
from .core import format, parse, query
from .anki import Recorder
from datetime import datetime
from . import resources_rc
#import os


class Input(QLineEdit):

    def __init__(self, changed):
        super(Input, self).__init__()
        self.changed = changed

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.changed(self.text())
        super(Input, self).keyPressEvent(e)


class SignalObject(QObject):
    """Provide signal functionality to QRunnable."""

    sig = pyqtSignal(bool)

    def emit(self, *args):
        self.sig.emit(*args)

    def connect(self, *args):
        self.sig.connect(*args)


class Runnable(QRunnable):
    """Wrap ``fn`` in a mutex and emit signal using the return value of
    ``fn``."""

    mutex = QMutex()

    def __init__(self, fn):
        super(Runnable, self).__init__()
        self.fn = fn
        self.finished = SignalObject()

    def run(self):
        with QMutexLocker(self.mutex):
            self.finished.emit(self.fn())


class Settings(object):

    def __init__(self):
        self.settings = QSettings('helanic', 'memoit')
        self.groupname = 'anki'

    def get(self, key):
        self.settings.beginGroup(self.groupname)
        try:
            return self.settings.value(key, '')
        finally:
            self.settings.endGroup()

    def set(self, key, value):
        self.settings.beginGroup(self.groupname)
        try:
            self.settings.setValue(key, value)
        finally:
            self.settings.endGroup()

    @property
    def username(self):
        return self.get('username')

    @username.setter
    def username(self, value):
        return self.set('username', value)

    @property
    def password(self):
        return self.get('password')

    @password.setter
    def password(self, value):
        return self.set('password', value)

    @property
    def deck(self):
        return self.get('deck')

    @deck.setter
    def deck(self, value):
        return self.set('deck', value)


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
        self.settings = Settings()
        self.settings_dialog = SettingsDialog(self.settings)
        self.settings_dialog.accepted.connect(self.login)

        # main window
        self.setWindowTitle('memoit')
        output_edit = QTextEdit()
        output_edit.setReadOnly(True)
        output_edit.setFont(QFont('Lucida Sans Unicode'))
        input_edit = Input(lambda s: output_edit.setText(trans(s, self.record)))
        layout = QVBoxLayout()
        layout.addWidget(input_edit)
        layout.addWidget(output_edit)
        self.setLayout(layout)

        # tray
        self.tray = Tray(QIcon(':/tray.png'), self)
        self.tray.show()

        # must after settings set up
        self.try_login()

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
        assert self.settings.username, 'Invalid username.'

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


def trans(word, record):
    s = parse(query(word))
    record(s)
    return format(s)


#def fix_tray_icon():
    #"""Fix tray icon problem under Win7.

    #See `http://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon`_
    #for details.
    #"""
    #import ctypes
    #appid = 'answeror.memoit'
    #ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)


def main(argv):
    #fix_tray_icon()

    app = QApplication(argv)
    # don't know why
    app.setWindowIcon(QIcon(':/taskbar.png'))
    win = Window()
    win.show()
    return app.exec_()


if __name__ == '__main__':
    import sys
    main(sys.argv)