# Generate delta update file between two versions

from hashlib import sha256
from io import BytesIO
from os.path import join as pathjoin
from zipfile import ZipFile

from util import ALL_ZIP_NAMES


def zip_contains_dir(zf: ZipFile, path):
    """Recursively check whether zf contains directory specified by path.

    Returns False if the dir or any parent dirs do not exist. Otherwise returns True.
    """
    if path.endswith('/'):
        path = path[:-1]  # directories end with /, but don't want that here

    # splits to either [parent_path, dir_name] or [dir_name],
    # depending on whether there is a parent directory.
    parts = path.rsplit('/', maxsplit=1)
    if len(parts) == 2:
        parent_path, dir_name = parts
        if not zip_contains_dir(zf, parent_path):
            return False

    # either path is at root of dir or all parents exist, so now check the dir at path
    try:
        zf.getinfo(path + '/')
        return True
    except KeyError:
        return False

def dirs_and_files_for_zipfile(zf: ZipFile, ignore_if_no_dir=False) -> (dict, dict):
    """Return dictionary of directory name to ZipInfo for all directories and
    dictionary of filename to (ZipInfo, sha256 hash) for all files in zip file.

    ignore_if_no_dir: omit files that are missing directory entries.
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

    if ignore_if_no_dir:
        for f in list(files.keys()):
            # ensure all parents exist and remove from files dict if not
            parts = f.rsplit('/', maxsplit=1)
            if len(parts) > 1 and not zip_contains_dir(zf, parts[0]):
                print(f'Warning ({zf.filename}):\n  "{f}" ignored due to missing parent directory.')
                del files[f]

    return (dirs, files)

def dirs_and_files_for_full_version(path: str, ignore_if_no_dir=False) -> (dict, dict):
    """Return dictionary of directory name to ZipInfo for all directories and
    dictionary of filename to (ZipInfo, sha256 hash) for all files in zip files
    corresponding to given verison path.

    ignore_if_no_dir: omit files that are missing directory entries.
    """
    # collect details of all files, as they should exist in game's local copy to avoid
    # potential issues with moved/duplicated files that won't really be applied in fresh
    # downloads (ensuring deltas match that behaviour makes it more likely to find issues)
    dirs = {}
    files = {}

    for zipname in ALL_ZIP_NAMES:
        zippath = pathjoin(path, zipname)
        zf = ZipFile(zippath, 'r')
        sub_dirs, sub_files = dirs_and_files_for_zipfile(zf, ignore_if_no_dir)
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
    print('Enumerating version contents...')

    old_path = pathjoin(resource_path, str(ver_old))
    old_dirs, old_files = dirs_and_files_for_full_version(old_path, ignore_if_no_dir=True)
    print(f'{ver_old}: total {len(old_dirs)} directories, {len(old_files)} files')

    new_path = pathjoin(resource_path, str(ver_new))
    new_dirs, new_files = dirs_and_files_for_full_version(new_path, ignore_if_no_dir=False)
    print(f'{ver_new}: total {len(new_dirs)} directories, {len(new_files)} files')

    print('Scanning for changes between versions...')
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
