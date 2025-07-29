# Disable most in-app purchases by generating an update with empty jewel and pass shops.

import json

from util import ALL_ZIP_NAMES, encrypt_replacements_json, read_json_decrypted, \
                 replace_files_in_ver


IAP_FILES = [
    'json/master_campaign_banner.json',
    'json/master_campaign_detail.json',
    'json/master_jewel_shop.json',
    'json/master_login_purchase_detail.json'
]


def first_row_only(json_str):
    """Discard all JSON data except the first row (header) from input string"""
    json_data = json.loads(json_str)
    json_data = [json_data[0]]
    json_str = json.dumps(json_data)
    return json_str


def disable_iap(resource_path, ver):
    file_strs = {x: read_json_decrypted(resource_path, ver, x) for x in IAP_FILES}
    replacements = encrypt_replacements_json(
        {k: first_row_only(v).encode('utf-8') for k, v in file_strs.items()})
    replace_files_in_ver(resource_path, ver, replacements)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python disable_iap.py <resource_path> <ver>')
        print('Example: python disable_iap.py res 731')
        exit()

    disable_iap(argv[1], int(argv[2]))
