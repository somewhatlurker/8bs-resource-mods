# Re-encrypt all encrypted JSON files in given resource version with new key.

from os import listdir
from os.path import join as path_join

from recrypt_zip import recrypt_zip


def recrypt_ver(resource_path, ver):
    """Re-encrypt all .zip files for given version, overwriting them with new files."""
    ver_path = path_join(resource_path, str(ver))
    zip_paths = [path_join(ver_path, x) for x in listdir(ver_path)]
    for z in zip_paths:
        recrypt_zip(z)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python recrypt_ver.py <resource_path> <ver>')
        print('Example: python recrypt_ver.py res 730')
        exit()

    recrypt_ver(argv[1], int(argv[2]))
