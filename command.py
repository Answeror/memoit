#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: command
    :synopsis: Some command used to build pyqt.

.. moduleauthor:: Answeror <answeror@gmail.com>

These code was borrowed from `https://bitbucket.org/jbmohler/pyhacc/src/b0ad3a0b1e58/setup.py`_.

"""

import os
import distutils
from distutils.core import Command
from cx_Freeze import build


def needsupdate(src, targ):
    return not os.path.exists(targ) or os.path.getmtime(src) > os.path.getmtime(targ)


class PySideUiBuild:
    def qrc(self, qrc_file, py_file):
        import subprocess
        rccprocess = subprocess.Popen(['pyside-rcc', qrc_file, '-py3', '-o', py_file])
        rccprocess.wait()

    def uic(self, ui_file, py_file):
        import subprocess
        rccprocess = subprocess.Popen(['pyside-uic', ui_file, '-o', py_file])
        rccprocess.wait()


class PyQt4UiBuild:
    def qrc(self, qrc_file, py_file):
        import subprocess
        rccprocess = subprocess.Popen(['pyrcc4', qrc_file, '-py3', '-o', py_file])
        rccprocess.wait()

    def uic(self, ui_file, py_file):
        from PyQt4 import uic
        fp = open(py_file, 'w')
        uic.compileUi(ui_file, fp)
        fp.close()


class QtUiBuild(Command, PyQt4UiBuild):
    description = "build Python modules from Qt Designer .ui files"

    user_options = []
    ui_files = []
    qrc_files = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def compile_ui(self, ui_file, py_file):
        if not needsupdate(ui_file, py_file):
            return
        print("compiling %s -> %s" % (ui_file, py_file))
        try:
            self.uic(ui_file, py_file)
        except Exception as e:
            raise distutils.errors.DistutilsExecError('Unable to compile user interface %s' % str(e))
            return

    def compile_qrc(self, qrc_file, py_file):
        if not needsupdate(qrc_file, py_file):
            return
        print("compiling %s -> %s" % (qrc_file, py_file))
        try:
            self.qrc(qrc_file, py_file)
        except Exception as e:
            raise distutils.errors.DistutilsExecError('Unable to compile resource file %s' % str(e))
            return

    def run(self):
        for f in self.ui_files:
            dir, basename = os.path.split(f)
            self.compile_ui(f, os.path.join(dir, "ui_" + basename.replace(".ui", ".py")))
        for f in self.qrc_files:
            dir, basename = os.path.split(f)
            self.compile_qrc(f, os.path.join(dir, basename.replace(".qrc", "_rc.py")))

QtUiBuild.ui_files = []
QtUiBuild.qrc_files = [os.path.join(dir, f) \
                for dir in ['memoit'] \
                for f in os.listdir(dir) if f.endswith('.qrc')]


class Build(build):
    sub_commands = [('build_ui', None)] + build.sub_commands


cmds = {
        'build': Build,
        'build_ui': QtUiBuild,
       }
