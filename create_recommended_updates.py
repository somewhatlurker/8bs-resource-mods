APK_PATH = 'apk/game.apk'
RESOURCE_PATH = 'res'
TUTORIAL2_PATH = 'tutorial/tutorial_2.zip'


def update_already_exists(ver):
    """Returns true if files already exist for given update."""
    from os.path import exists as path_exists, join as path_join
    return path_exists(path_join(RESOURCE_PATH, str(ver)))


def read_apk_json_dir():
    """Read the bytes content of all files in the game .apk file's json directory.

    Returns dictionary of filename: content pairs.
    Prepended `assets/` is automatically removed.
    """
    from zipfile import ZipFile

    zf = ZipFile(APK_PATH, 'r')
    out = {}

    for f in zf.infolist():
        if f.is_dir():
            # ignore dirs
            continue
        elif f.filename.startswith('assets/json/'):
            out[f.filename[7:]] = zf.read(f)

    zf.close()
    return out


def upd_tutorial2():
    """Applies the tutorial update, overwriting the original tutorial_2.zip file.

    The tutorial must have files from the game client merged, then be re-encrypted with a
    key we control.

    (Don't worry about overwriting it, tutorial_2 contains nothing of real value.)
    """
    from recrypt_zip import recrypt_zip
    from util import replace_files_in_zip

    # 1. Extract the `json` directory from the game's .apk file (inside `assets` dir),
    # add it to `tutorial_2.zip`
    replace_files_in_zip(TUTORIAL2_PATH, read_apk_json_dir(), if_exists=False)

    # 2. `python recrypt_zip.py tutorial/tutorial_2.zip`
    recrypt_zip(TUTORIAL2_PATH)


def upd_730():
    """Creates update 730, based on 729 (last official version).

    Version 730 takes original data and re-encrypts it with a key we control (no other
    changes).
    """
    from os.path import join as path_join
    from gen_delta_update import gen_delta_update
    from new_ver import new_ver
    from recrypt_ver import recrypt_ver
    from util import replace_files_in_zip

    # 1. `python new_ver.py res 729 730`
    new_ver(RESOURCE_PATH, 729, 730)

    # 2. Copy `master_system` (both .json and .c) from the game's .apk file into
    # `res/730/1_json01.zip`, and `master_music3001_1` into `res/730/1_json03.zip`
    json_dir = read_apk_json_dir()

    replacements = {
        'json/master_system.json': json_dir['json/master_system.json'],
        'json/master_system.c': json_dir['json/master_system.c']
    }
    zip_path = path_join(RESOURCE_PATH, '730', '1_json01.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

    replacements = {
        'json/master_music3001_1.json': json_dir['json/master_music3001_1.json'],
        'json/master_music3001_1.c': json_dir['json/master_music3001_1.c']
    }
    zip_path = path_join(RESOURCE_PATH, '730', '1_json03.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

    # 3. `python recrypt_ver.py res 730`
    recrypt_ver(RESOURCE_PATH, 730)

    # 4. `python gen_delta_update.py res 729 730`
    gen_delta_update(RESOURCE_PATH, 729, 730)


def upd_731():
    """Creates update 731, based on 730.

    Version 731 disables in-app purchases, as they cannot be supported without
    re-publishing the app in app stores.
    """
    from disable_iap import disable_iap
    from gen_delta_update import gen_delta_update
    from new_ver import new_ver

    # 1. `python new_ver.py res 730 731`
    new_ver(RESOURCE_PATH, 730, 731)

    # 2. `python disable_iap.py res 731`
    disable_iap(RESOURCE_PATH, 731)

    # 3. `python gen_delta_update.py res 730 731`
    gen_delta_update(RESOURCE_PATH, 730, 731)


def upd_732():
    """Creates update 732, based on 731.

    Version 732 creates an eternal exchange event (BIT festa), so players can obtain
    event cards and rewards.
    """
    from gen_delta_update import gen_delta_update
    from make_eternal_exchange_event import make_eternal_exchange_event
    from new_ver import new_ver

    # 1. `python new_ver.py res 731 732`
    new_ver(RESOURCE_PATH, 731, 732)

    # 2. `python make_eternal_exchange_event.py res 732`
    make_eternal_exchange_event(RESOURCE_PATH, 732)

    # 3. `python gen_delta_update.py res 731 732`
    gen_delta_update(RESOURCE_PATH, 731, 732)


if __name__ == '__main__':
    from os.path import exists as path_exists, join as path_join
    from util import ALL_ZIP_NAMES

    # check necessary files exist
    needed_files = [APK_PATH, TUTORIAL2_PATH]
    for name in ALL_ZIP_NAMES:
        needed_files.append(path_join(RESOURCE_PATH, '729', name))
    for name in needed_files:
        if not path_exists(name):
            print(f'Missing file "{name}" - updates cannot be generated')
            exit(1)

    # tutorial
    print('tutorial_2:')
    upd_tutorial2()
    print('tutorial_2 updated\n')

    # resource updates
    resource_updates = [
        (730, upd_730),
        (731, upd_731),
        (732, upd_732),
    ]

    for ver, fn in resource_updates:
        if update_already_exists(ver):
            print(f'Resource version {ver} already exists - skipping\n')
            continue
        print(f'{ver}:')
        fn()
        print(f'Resource version {ver} completed\n')
