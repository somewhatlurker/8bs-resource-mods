# Makes gacha tickets last for six months (instead of 15 days)

import json

from util import encrypt_replacements_json, read_json_decrypted, replace_files_in_ver


def increase_gacha_ticket_expiry(resource_path, ver):
    item_table = json.loads(read_json_decrypted(resource_path, ver, 'json/master_time_limit_item.json'))
    detail_table = json.loads(read_json_decrypted(resource_path, ver, 'json/master_time_limit_item_detail5.json'))

    for item in item_table:
        if item['SYSTEM'] != 5:
            continue  # ignore anything that isn't a gacha ticket
        item_id = item['ID']
        detail = next(x for x in detail_table if x['ID'] == item_id)
        detail['PERIOD'] = 183
        item['DESC'] = item['DESC'].replace('15日', '6月')

    replacements = encrypt_replacements_json({
        'json/master_time_limit_item.json': json.dumps(item_table).encode('utf-8'),
        'json/master_time_limit_item_detail5.json': json.dumps(detail_table).encode('utf-8')
    })
    replace_files_in_ver(resource_path, ver, replacements)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python increase_gacha_ticket_expiry.py <resource_path> <ver>')
        print('Example: python increase_gacha_ticket_expiry.py res 735')
        exit()

    increase_gacha_ticket_expiry(argv[1], int(argv[2]))
