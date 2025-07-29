from io import BytesIO
from os.path import join as path_join
from zipfile import ZipFile

from crypto import decrypt_json, encrypt_json_bytes_aeskey, encrypt_new_aes_key, \
                   gen_new_aes_key


# name of all resource zip files, in order downloaded/extracted by the game on install
ALL_ZIP_NAMES = ['1_bg.zip', '1_card160.zip', '1_card640.zip', '1_effect.zip',
                 '1_icon.zip', '1_stand.zip', '1_movie.zip', '1_sound.zip', '1_ssbp.zip',
                 '1_json01.zip', '1_json02.zip', '1_json03.zip', '1_pkg.zip']


def read_file(resource_path, ver, name, zips=ALL_ZIP_NAMES):
    """Read file `name` from given version's resources.

    `zips` can be used to limit what .zip archives are searched.
    Later specified archives take priority.

    Returns None if file not found in any archive.
    Returns bytes if file was found.
    """
    ver_path = path_join(resource_path, str(ver))
    zip_paths = [path_join(ver_path, x) for x in reversed(zips)]
    for path in zip_paths:
        z = ZipFile(path, 'r')
        try:
            return z.read(name)
        except KeyError:
            continue
    return None


def read_json_decrypted(resource_path, ver, name, zips=ALL_ZIP_NAMES):
    """Read encrypted JSON file `name` from given version's resources,
    decrypted to string.

    `zips` can be used to limit what .zip archives are searched.
    Later specified archives take priority.

    Returns None if file not found in any archive.
    Returns str if file was found.
    """
    assert name[-5:] == '.json'

    json_bytes = read_file(resource_path, ver, name, zips)
    if not json_bytes:
        return None

    c_bytes = read_file(resource_path, ver, name[:-5] + '.c', zips)
    if not c_bytes:
        return None

    return decrypt_json(json_bytes, c_bytes)


def replace_files_in_zip(zip_path, replacements, if_exists=True):
    """Replace some files in existing .zip archive with new version.

    replacements should be a dictionary of {filename: data} pairs, e.g.:
    `{'file.txt': 'contents'}` (data is str or bytes)

    When if_exists is true, only pre-existing files in the archive are replaced
    (new files are not created).

    Output will overwrite original input file.
    """
    zip_in = ZipFile(zip_path, 'r')
    namelist_in = zip_in.namelist()

    if if_exists:
        has_any_replacements = False
        for r in replacements.keys():
            if r in namelist_in:
                has_any_replacements = True
                break

        if not has_any_replacements:
            # skip processing - no matching files
            return

    out_buf = BytesIO()
    zip_out = ZipFile(out_buf, 'w')

    for f in zip_in.infolist():
        if f.is_dir():
            zip_out.mkdir(f)
            continue
        elif f.filename not in replacements:
            # Write directly to output
            zip_out.writestr(f, zip_in.read(f))
            continue
        else:
            # Replace contents as file is confirmed to exist in original archive
            zip_out.writestr(f, replacements[f.filename])

    if not if_exists:
        # Insert newly added files
        new_files = [
            (f, data) for f, data in replacements.items()
            if f not in namelist_in
        ]
        for f, data in new_files:
            zip_out.writestr(f, data)

    zip_in.close()
    zip_out.close()

    with open(zip_path, 'wb') as f:
        f.write(out_buf.getbuffer())


def replace_files_in_ver(resource_path, ver, replacements, zips=ALL_ZIP_NAMES):
    """Replace some files in given version's resources.

    replacements should be a dictionary of {filename: data} pairs, e.g.:
    `{'file.txt': 'contents'}` (data is str or bytes)

    `zips` can be used to limit what .zip archives are modified.
    Output will overwrite original input file.

    Only pre-existing files in the archive are replaced (new files are not created).
    """
    ver_path = path_join(resource_path, str(ver))
    zip_paths = [path_join(ver_path, x) for x in zips]
    for path in zip_paths:
        replace_files_in_zip(path, replacements, if_exists=True)


def encrypt_replacements_json(replacements):
    """Generate new keys and encrypt data for all .json files in replacements.

    Replacements should contain unencrypted strings or bytes,
    similar to other functions here.
    `{'file.json': 'contents'}`

    Final returned value contains new .json and .c file pairs, as well as unmodified
    data for any non-JSON files.
    """
    out = {}
    for k, v in replacements.items():
        if not k.endswith('.json'):
            out[k] = content
            continue

        if isinstance(v, str):
            v = v.encode('utf-8')

        aeskey = gen_new_aes_key(v)
        out[k] = encrypt_json_bytes_aeskey(v, aeskey)
        out[k[:-5] + '.c'] = encrypt_new_aes_key(aeskey)
    return out
