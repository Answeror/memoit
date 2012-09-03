#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cx_Freeze import setup, Executable
from command import cmds


includes = [
        'lxml',
        'lxml._elementpath',
        'gzip',
        'inspect'
        ]
excludes = [
        'BeautifulSoup',
        'UserDict',
        '_posixsubprocess',
        'htmlentitydefs',
        'paste.proxy',
        'sets',
        'urllib.urlencode',
        'urllib.urlopen',
        'urllib2',
        'urlparse',
        'webob'
        ]

setup(
        name='memoit',
        version='0.0.2dev',
        packages=['memoit'],
        cmdclass=cmds,
        options={
            'build_exe': {
                'includes': includes,
                'excludes': excludes
                }
            },
        executables=[Executable(
            'main.py',
            base='Win32GUI',
            targetName='memoit.exe',
            compress=True,
            icon='memoit/icons/64.ico'
            )]
        )
