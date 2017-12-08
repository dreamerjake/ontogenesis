# -*- coding: utf-8 -*-
"""
Built using dev branch 'v5.x' of cx_Freeze

git clone https://github.com/anthony-tuininga/cx_Freeze.git
git checkout v5.x
C:\\ProgramData\\Anaconda3\\python -m pip install .

in current dir:
python cx_setup.py build

"""

import opcode
import os
import sys

from cx_Freeze import setup, Executable


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


base = 'Win32GUI' if sys.platform == 'win32' else None

# venv stuff
distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
python_install_path = os.path.join(distutils_path, '..', '..')
os.environ['TCL_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tk8.6')

build_exe_options = {
    'includes': [],
    'include_files': ['assets/'],
    'packages': ['pygame']
}

game_exe = Executable(
    script='game.py',
    base=base,
    targetName='ontogenesis.exe'
)

setup(
    name='ontogenesis',
    options={
        'build_exe': build_exe_options
    },
    version='0.1',
    author='Jake Silverman',
    author_email='jacobsilverman85@gmail.com',
    executables=[game_exe]
)
