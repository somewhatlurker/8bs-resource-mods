# Adds level limit increase (break) items for 2_wEi and BAC members.

import json
from os.path import join as path_join

from util import encrypt_replacements_json, read_file, read_json_decrypted, \
                 replace_files_in_ver, replace_files_in_zip

# ID: name
GIRLS_TO_ADD = {
    10: 'かなで',
    11: 'アルミ',
    12: 'ミント',
    13: 'アモル',
    14: 'クゥエル',
    15: 'ベル'
}


def add_extra_limitbreak_items(resource_path, ver):
    item_table = json.loads(read_json_decrypted(resource_path, ver, 'json/master_sub_item.json'))
    detail_table = json.loads(read_json_decrypted(resource_path, ver, 'json/master_sub_item_detail7.json'))
    tl_item_table = json.loads(read_json_decrypted(resource_path, ver, 'json/master_time_limit_item.json'))

    hinata_item = next(x for x in item_table if x['NAME'] == '上限突破 Ver.ひなた')
    mei_item = next(x for x in item_table if x['NAME'] == '上限突破 Ver.メイ')
    max_id = max([i['ID'] for i in item_table[1:]])

    new_id_start = max_id + 1
    new_order_start = mei_item['ORDER'] + 1

    # make space in the table for new items
    for item in item_table[1:]:
        if item['ORDER'] >= new_order_start:
            item['ORDER'] += len(GIRLS_TO_ADD)

    # fixup order field of master_time_limit_item, which is part of the same
    # sequence
    for item in tl_item_table[1:]:
        if item['ORDER'] >= new_order_start:
            item['ORDER'] += len(GIRLS_TO_ADD)

    image_replacements = {}
    for i, girl in enumerate(GIRLS_TO_ADD.items()):
        item_id = new_id_start + i
        order = new_order_start + i

        item_row = {
            'ID': item_id, 'ORDER': order, 'NAME': f'上限突破 Ver.{girl[1]}',
            'PLAY_RARE_FRAG': 0, 'DESC': f'{girl[1]}の最大Lvを上げるアイテム。所持最大個数は100個',
            'SYSTEM': 7, 'MAX': 100
        }
        item_table.append(item_row)

        detail_row = {
            'ID': item_id, 'NAME': f'上限突破 Ver.{girl[1]}', 'GIRL_ID': girl[0],
            'UP_N': 0, 'UP_R': 10, 'UP_SR': 5, 'UP_UR': 2
        }
        detail_table.append(detail_row)

        # temporary: just copy hinata's images
        hinata_img = read_file(resource_path, ver,
                               f'image/item/item1_{hinata_item["ID"]}.png',
                               zips=['1_pkg.zip'])
        hinata_img40 = read_file(resource_path, ver,
                                f'image/item/item40_1_{hinata_item["ID"]}.png',
                                zips=['1_pkg.zip'])
        hinata_img94 = read_file(resource_path, ver,
                                f'image/item/item94_1_{hinata_item["ID"]}.png',
                                zips=['1_pkg.zip'])

        image_replacements[f'image/item/item1_{item_id}.png'] = hinata_img
        image_replacements[f'image/item/item40_1_{item_id}.png'] = hinata_img40
        image_replacements[f'image/item/item94_1_{item_id}.png'] = hinata_img94


    replacements = encrypt_replacements_json({
        'json/master_sub_item.json': json.dumps(item_table).encode('utf-8'),
        'json/master_sub_item_detail7.json': json.dumps(detail_table).encode('utf-8'),
        'json/master_time_limit_item.json': json.dumps(tl_item_table).encode('utf-8')
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # add new images to 1_pkg.zip
    zip_path = path_join(resource_path, str(ver), '1_pkg.zip')
    replace_files_in_zip(zip_path, image_replacements, if_exists=False)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python add_extra_limitbreak_items.py <resource_path> <ver>')
        print('Example: python add_extra_limitbreak_items.py res 735')
        exit()

    add_extra_limitbreak_items(argv[1], int(argv[2]))
