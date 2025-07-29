# Generate delta update file between two versions

from hashlib import sha256
from io import BytesIO
from os.path import join as pathjoin
from zipfile import ZipFile

from util import ALL_ZIP_NAMES


def dirs_and_files_for_zipfile(zf: ZipFile) -> (dict, dict):
    """Return dictionary of directory name to ZipInfo for all directories and
    dictionary of filename to (ZipInfo, sha256 hash) for all files in zip file.
    """
    dirs = {}
    files = {}

    for f in zf.infolist():
        fname = f.filename
        if f.is_dir():
            dirs[fname] = f
        else:
            fhash = sha256(zf.read(f)).digest()
            files[fname] = (f, fhash)

    return (dirs, files)

def dirs_and_files_for_full_version(path: str) -> (dict, dict):
    """Return dictionary of directory name to ZipInfo for all directories and
    dictionary of filename to (ZipInfo, sha256 hash) for all files in zip files
    corresponding to given verison path.
    """
    # collect details of all files, as they should exist in game's local copy to avoid
    # potential issues with moved/duplicated files that won't really be applied in fresh
    # downloads (ensuring deltas match that behaviour makes it more likely to find issues)
    dirs = {}
    files = {}

    for zipname in ALL_ZIP_NAMES:
        zippath = pathjoin(path, zipname)
        zf = ZipFile(zippath, 'r')
        sub_dirs, sub_files = dirs_and_files_for_zipfile(zf)
        zf.close()

        dirs.update(sub_dirs)
        files.update(sub_files)

    return (dirs, files)

def get_file_list_contents(path: str, files: [str]) -> dict:
    """Return dictionary of filename to file content (bytes) for each file in list.
    File content is taken from update zip files at path.
    """
    contents = {}

    for zipname in ALL_ZIP_NAMES:
        zippath = pathjoin(path, zipname)
        zf = ZipFile(zippath, 'r')

        for fname in files:
            try:
                contents[fname] = zf.read(fname)
            except KeyError:
                continue

    return contents


def gen_delta_update(resource_path, ver_old, ver_new):
    print(f'Generating delta update from {ver_old} to {ver_new}...')
    print('Scanning for changes between versions...')

    old_path = pathjoin(resource_path, str(ver_old))
    old_dirs, old_files = dirs_and_files_for_full_version(old_path)

    new_path = pathjoin(resource_path, str(ver_new))
    new_dirs, new_files = dirs_and_files_for_full_version(new_path)

    created_dirs = {k: v for k, v in new_dirs.items()
                    if k not in old_dirs}
    modified_files = {k: v for k, v in new_files.items()
                      if old_files.get(k, (None, None))[1] != v[1]}
    deleted_files = [k for k in old_files.keys()
                     if k not in new_files]

    print('Done!')
    print(f'  Created dirs: {len(created_dirs)}')
    print(f'  Modified files: {len(modified_files)}')
    print(f'  Deleted files: {len(deleted_files)}')
    print()

    print('Loading modified files...')
    new_contents = get_file_list_contents(new_path, modified_files.keys())
    print('Done!')
    print()

    print('Writing output...')
    out_path = pathjoin(new_path, str(ver_old+1)) + '.zip'
    zf = ZipFile(out_path, 'w')
    for k, v in created_dirs.items():
        zf.mkdir(v)
    for k, v in modified_files.items():
        zf.writestr(v[0], new_contents[k])
    for k in deleted_files:
        zf.writestr(k, b'')  # replace with empty file to free up space on user devices
    zf.close()
    print('Done!')


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 4:
        print('Usage: python gen_delta_update.py <resource_path> <ver_old> <ver_new>')
        print('Example: python gen_delta_update.py res 729 730')
        exit()

    gen_delta_update(argv[1], int(argv[2]), int(argv[3]))
