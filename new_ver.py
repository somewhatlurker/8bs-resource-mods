# Copy base (non-delta) .zip files from old version to new version dir,
# and update version.json.

from os import makedirs
from os.path import join as path_join
from shutil import copy2

from util import ALL_ZIP_NAMES, replace_files_in_zip


def copy_all_zips(ver_path_old, ver_path_new):
    """Copies all base .zip files (ALL_ZIP_NAMES) from old dir to new dir"""
    for z in ALL_ZIP_NAMES:
        z_old = path_join(ver_path_old, z)
        z_new = path_join(ver_path_new, z)
        copy2(z_old, z_new)


def update_version(ver_path, ver):
    """Updates version.json in 1_pkg.zip to reflect the new version."""
    zip_path = path_join(ver_path, '1_pkg.zip')
    replacements = {'version.json': f'[{{"version":{ ver }}}]'}
    replace_files_in_zip(zip_path, replacements)


def new_ver(resource_path, ver_old, ver_new):
    ver_path_old = path_join(resource_path, str(ver_old))
    ver_path_new = path_join(resource_path, str(ver_new))

    makedirs(ver_path_new)
    copy_all_zips(ver_path_old, ver_path_new)
    update_version(ver_path_new, ver_new)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 4:
        print('Usage: python new_ver.py <resource_path> <ver_old> <ver_new>')
        print('Example: python new_ver.py res 729 730')
        exit()

    new_ver(argv[1], int(argv[2]), int(argv[3]))
