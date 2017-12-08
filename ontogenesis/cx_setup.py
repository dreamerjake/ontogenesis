# import distutils
import opcode
import os
import sys

from cx_Freeze import setup, Executable

# sys.path.append(os.path.join(os.path.dirname(__file__), 'ontogenesis'))


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


base = 'Win32GUI' if sys.platform == 'win32' else None

distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
python_install_path = os.path.join(distutils_path, '..', '..')

os.environ['TCL_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(python_install_path, 'tcl', 'tk8.6')

# print(distutils_path)

build_exe_options = {
    # 'include_files': [
    #     (distutils_path, 'distutils'),
    #     # 'game',
    #     # 'ontogenesis\helpers.py',
    #     # 'ontogenesis\game.py',
    #     # 'ontogenesis\map.py',
    #     # 'ontogenesis\player.py',
    #     # 'ontogenesis\settings.py',
    #     # 'ontogenesis\\ui.py',
    #     # 'ontogenesis\enemy.py',
    #     # 'ontogenesis\skill.py'
    # ],
    'includes': [],
    'include_files': ['assets/'],
    # 'excludes': ['distutils'],
    'packages': ['pygame'],
    # 'path': sys.path + ['ontogenesis']
}

# options = {
#     'build_exe': {
#         'packages': ['pygame'],
#     },
# }

game_exe = Executable(
    script='game.py',
    # initScript=None,
    base=base,
    # targetDir=r"dist",
    targetName='targetName.exe',
    # compress=True,
    # copyDependentFiles=True,
    # appendScriptToExe=False,
    # appendScriptToLibrary=False,
    # icon=None
)

setup(
    name='ontogenesis',
    options={
        'build_exe': build_exe_options
    },
    version='0.1',
    description='test description',
    author='Jake Silverman',
    author_email='jacobsilverman85@gmail.com',
    executables=[game_exe]
)
