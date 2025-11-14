# Delete full resource files except for earliest and latest version.
# Incremental update files are kept for for all versions.

from os import listdir, remove
from os.path import isdir, isfile, join as path_join


def list_full_version_files(res_path, ver):
    """Returns list of full update filenames belonging to given version.

    Full update files meaning non-incremental.
    """
    def file_is_from_full(filename):
        """Returns whether the file with given name belongs to a full update."""
        return filename.startswith('1_') and filename.endswith('.zip')

    ver_path = path_join(res_path, str(ver))
    ver_files = [x for x in listdir(ver_path) if isfile(path_join(ver_path, x))]
    full_files = [x for x in ver_files if file_is_from_full(x)]
    return full_files


def list_all_versions(res_path):
    """Returns list of all versions in res_path, as integer version numbers.

    List is sorted in ascending order.
    """
    strlist = [x for x in listdir(res_path) if isdir(path_join(res_path, x))]
    intlist = [int(x) for x in strlist if x.isdigit()]
    intlist.sort()
    return intlist


def list_full_versions(res_path):
    """Returns list of full versions in res_path, as integer version numbers.

    Full versions means versions that contain all of the non-incremental files.
    List is sorted in ascending order.
    """

    verlist = list_all_versions(res_path)
    fulllist = []

    for ver in verlist:
        full_files = list_full_version_files(res_path, ver)
        if len(full_files) >= 13:  # only count if *all* files are present
            fulllist.append(ver)

    return fulllist


def delete_unneeded_full_res(resource_path):
    full_vers = list_full_versions(resource_path)
    if len(full_vers) <= 2:
        # nothing to do if only have two or fewer full versions
        return

    vers_to_delete = full_vers[1:-1]
    print('Deleting non-incremental files for', vers_to_delete)

    for ver in vers_to_delete:
        ver_path = path_join(resource_path, str(ver))
        files_to_delete = list_full_version_files(resource_path, ver)

        for f in files_to_delete:
            file_path = path_join(ver_path, f)
            remove(file_path)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 2:
        print('Usage: python delete_unneeded_full_res.py <resource_path>')
        print('Example: python delete_unneeded_full_res.py res')
        exit()

    delete_unneeded_full_res(argv[1])
