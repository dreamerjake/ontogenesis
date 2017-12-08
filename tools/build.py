# coding=utf-8
"""
autogenerate the lines for game.SED and install.bat
"""

import glob
import os

dirs = []
files = []
paths = []

lib_path = 'C:/Users/Jake/PycharmProjects/ontogenesis/ontogenesis/build/exe.win-amd64-3.6/lib/'

for name in glob.glob('C:/Users/Jake/PycharmProjects/ontogenesis/ontogenesis/build/exe.win-amd64-3.6/lib/**/*', recursive=True):
    # print(name)
    path, file = os.path.split(name)
    if os.path.isdir(name):
        # print("DIR", path)
        dirs.append(os.path.relpath(name, lib_path))
        paths.append(name)
    else:
        files.append((file, os.path.relpath(path, lib_path)))
        # print(file, path)

for d in dirs:
    print('mkdir "%current_dir%lib\\{}"'.format(d))
for f in files:
    print('move /y {} "%current_dir%lib\\{}\\"'.format(f[0], f[1]))

counter = 0

for f in files:
    print('FILE{}="{}"'.format(33 + counter, f[0]))
    counter += 1

pathcounter = 0

for p in paths:
    print('SourceFiles{}={}'.format(9 + pathcounter, p))
    pathcounter += 1
