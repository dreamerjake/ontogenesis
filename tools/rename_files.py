# -*- coding: utf-8 -*-
import os


def rename_files(old, new, path='.', test=False):

    root, dirs, filenames = next(os.walk(path))

    for filename in filenames:
        name, ext = os.path.splitext(filename)
        if old in name:
            new_name = name.replace(old, new) + ext
            old_path = os.path.join(path, filename)
            new_path = os.path.join(path, new_name)
            print(f'{filename} => {new_name}')

            if not test:
                os.rename(old_path, new_path)
