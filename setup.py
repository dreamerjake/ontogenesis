import distutils
import opcode
import os

from cx_Freeze import setup, Executable

# C:\ProgramData\Anaconda3\python setup.py build

distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
python_install_path = os.path.join(distutils_path, '..', '..')

os.environ['TCL_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tk8.6')

print(distutils_path)

build_exe_options = {'include_files': [(distutils_path, 'distutils')], "excludes": ["distutils"]}

packages = ['pygame']
options = {
    'build_exe': {
        'packages': packages,
    },
}

setup(
    name='ontogenesis',
    options={'build_exe': build_exe_options},
    version='0.1',
    description='test description',
    executables=[Executable('ontogenesis.py', base=None)]
)