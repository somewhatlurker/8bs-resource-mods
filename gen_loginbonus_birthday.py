# Generate login bonuses for character birthdays.

from copy import deepcopy
from datetime import date, timedelta
from io import BytesIO
import json
import math
from os.path import join as path_join
from typing import Dict, List

from PIL import Image

from loginbonus_common.gen_loginbonus_image import gen_loginbonus_image
from util import encrypt_replacements_json, read_json_decrypted, \
                 replace_files_in_ver, replace_files_in_zip


try:
    import imagequant
    def image_quantize(image: Image) -> Image:
        return imagequant.quantize_pil_image(image, max_quality=90)
except ImportError:
    print('Warning: imagequant not installed, will use lower quality quantisation.')
    def image_quantize(image: Image) -> Image:
        return image.quantize()


CHARA_NAMES_JA = {
    1: '桜木ひなた',
    2: '水瀬鈴音',
    3: '神楽月',
    4: '橘彩芽',
    5: '姫咲杏梨',
    6: '星宮ゆきな',
    7: '源氏ほたる',
    8: 'メイ',
    9: '理事長',
    10: '空乃かなで',
    11: '虎牙アルミ',
    12: '虎牙ミント',
    13: 'アモル',
    14: 'クゥエル',
    15: 'ベル'
}

CHARA_NAMES_EN = {
    1: 'Hinata Sakuragi',
    2: 'Suzune Minase',
    3: 'Akari Kagura',
    4: 'Ayame Tachibana',
    5: 'Anri Himesaki',
    6: 'Yukina Hoshimiya',
    7: 'Hotaru Genji',
    8: 'Mei',
    9: 'Headmistress',
    10: 'Kanade Sorano',
    11: 'Alumi Koga',
    12: 'Mint Koga',
    13: 'Amor',
    14: 'Cwellan',
    15: 'Bellum'
}

CHARA_NAMES_SHORT_JA = {
    1: 'ひなた',
    2: '鈴音',
    3: '月',
    4: '彩芽',
    5: '杏梨',
    6: 'ゆきな',
    7: 'ほたる',
    8: 'メイ',
    9: '理事長',
    10: 'かなで',
    11: 'アルミ',
    12: 'ミント',
    13: 'アモル',
    14: 'クゥエル',
    15: 'ベル'
}

CHARA_NAMES_SHORT_EN = {
    1: 'Hinata',
    2: 'Suzune',
    3: 'Akari',
    4: 'Ayame',
    5: 'Anri',
    6: 'Yukina',
    7: 'Hotaru',
    8: 'Mei',
    9: 'Headmistress',
    10: 'Kanade',
    11: 'Alumi',
    12: 'Mint',
    13: 'Amor',
    14: 'Cwellan',
    15: 'Bellum'
}

CHARA_BIRTHDAYS = {
    1: date(1996, 11, 12),  # Hinata/Haruka Shamoto
    2: date(1991, 6, 12),  # Suzune/Ayami Yoshii
    3: date(1900, 5, 30),  # Akari/Yoshioka Misaki (unknown year)
    4: date(1900, 2, 2),  # Ayame/Natsuki Aono (unknown year)
    5: date(1994, 3, 1),  # Anri/Wakana Minami
    6: date(1994, 9, 8),  # Yukina/Azumi Waki
    7: date(1993, 1, 21),  # Hotaru/Nanami Yoshimura
    8: date(1996, 7, 28),  # Mei/Miharu Sawada
    9: date(1987, 2, 27),  # Headmistress/Rika Tachibana
    10: date(1994, 9, 13),  # Kanade/Ayaka Ohashi
    11: date(1995, 10, 2),  # Alumi/Maiko Nomura
    12: date(1993, 10, 14),  # Mint/Rana Morishita
    # 13: date(1996, 1, 22),  # Amor/Minami Tanaka
    # 14: date(1999, 12, 22),  # Cwellan/Tomori Kusunoki
    # 15: date(1900, 7, 29),  # Bellum/Chisa Suganuma (unknown year)
    13: date(1900, 1, 11),  # Amor (B.A.C birthdays are 1/11 rather than seiyuu's ones)
    14: date(1900, 1, 11),  # Cwellan
    15: date(1900, 1, 11),  # Bellum
    16: date(1994, 12, 3)  # Yui/Yu Serizawa (not actually in game's numbering)
}

CHARA_BIRTHDAY_BGS = {
    1: 'bg197',  # Birthday stage for all of 8/pLanet!!
    2: 'bg186',
    3: 'bg189',
    4: 'bg201',
    5: 'bg203',
    6: 'bg190',
    7: 'bg199',
    8: 'bg187',
    10: 'bg204',  # Kanade's room
    11: 'bg_live_42',  # Despair stage
    12: 'bg_live_42',  # Despair stage
    13: 'bg222',  # Dark church
    14: 'bg222',  # Dark church
    15: 'bg222',  # Dark church
}

CHARA_BIRTHDAY_IMAGE_CARDS = {
    1: 795,  # Last birthday series for all of 8/pLanet!!
    2: 780,
    3: 779,
    4: 809,
    5: 813,
    6: 792,
    7: 808,
    8: 788,
    10: 571,  # Idol Kanade
    11: 564,  # 1st anniversary 2_wEi
    12: 565,
    13: 644,  # Silent World B.A.C
    14: 645,
    15: 646
}

EVENT_DAYS = 5
EVENT_JEWELS_PER_DAY = 10

BIRTHDAY_BONUS_INFO = [
    {
        'DATE': date(1900, 1, 11), 'DURATION_DAYS': EVENT_DAYS,
        'CHARA_NAME_JA': 'B.A.Cメンバー', 'CHARA_NAME_EN': 'B.A.C Members',
        'CHARA_NAME_SHORT_JA': 'B.A.C', 'CHARA_NAME_SHORT_EN': 'B.A.C',
        'EVENT_NAME_JA': 'HappyBirthday', 'EVENT_NAME_EN': 'Happy Birthday',
        'BG': 'bg222',
        'CHARAS': (13, 14, 15),
        'IMAGE_CARDS': (CHARA_BIRTHDAY_IMAGE_CARDS.get(x) for x in (13, 14, 15))
    }
]
# Add all of 8/pLanet!!, 2_wEi, and Kanade (sorted by birthday)
for chara_id in (7, 4, 5, 3, 2, 8, 6, 10, 11, 12, 1):
    BIRTHDAY_BONUS_INFO.append({
        'DATE': CHARA_BIRTHDAYS[chara_id], 'DURATION_DAYS': EVENT_DAYS,
        'CHARA_NAME_JA': CHARA_NAMES_JA[chara_id],
        'CHARA_NAME_EN': CHARA_NAMES_EN[chara_id],
        'CHARA_NAME_SHORT_JA': CHARA_NAMES_SHORT_JA[chara_id] + 'ちゃん',
        'CHARA_NAME_SHORT_EN': CHARA_NAMES_SHORT_EN[chara_id],
        'EVENT_NAME_JA': 'HappyBirthday', 'EVENT_NAME_EN': 'Happy Birthday',
        'BG': CHARA_BIRTHDAY_BGS[chara_id],
        'CHARAS': (chara_id,),
        'IMAGE_CARDS': (CHARA_BIRTHDAY_IMAGE_CARDS.get(chara_id),)
    })

# copy, set BG, and set MESSAGE for each character
# (set for every item in list)
LOGIN_EVENT_DETAIL = [
    {
        'ID': x+1, 'DAY': x+1, 'BG': None,
        'PAGE': 1, 'X': 70 + x*120, 'Y': 67,
        'TITLE': f'コアジュエル × {EVENT_JEWELS_PER_DAY}', 'MESSAGE': None,
        'ITEM_TYPE': 0, 'ITEM_ID': 2, 'ITEM_NUM': EVENT_JEWELS_PER_DAY
    }
    for x in range(EVENT_DAYS)
]

HTML_TABLE_STRINGS_JA = {
    'date': '日付',
    'date_format': '%m月%d日',
    'character_name': 'キャラ',
    'rewards': '報酬',
    'n_jewels_for_d_days': '毎日コアジュエル{n}個 ({d}日間)'
}
HTML_TABLE_STRINGS_EN = {
    'date': 'Date',
    'date_format': '%m/%d',
    'character_name': 'Character',
    'rewards': 'Rewards',
    'n_jewels_for_d_days': '{n} core jewels per day ({d} days)'
}

HTML_TABLE_STYLE = '''<style>
    table.loginbonus-schedule-birthday {
        border: 2px solid black;
        border-spacing: 0;
        margin: 0.5em 0;
    }
    table.loginbonus-schedule-birthday th, table.loginbonus-schedule-birthday td {
        border: 1px solid black;
        padding: 0.05em 0.25em;
    }
</style>'''

def _gen_bg_image(
        info_dict: dict,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    bg_name = info_dict['BG']
    card_image_files = [f'image/chara/stand/stand_chara{id}_2.png' for id in info_dict['IMAGE_CARDS']]
    reward_image_files = [f'image/item/item94_{x["ITEM_TYPE"]}_{x["ITEM_ID"]}.png' for x in info_dict['EVENT_DETAIL']]
    reward_quantities = [x['ITEM_NUM'] for x in info_dict['EVENT_DETAIL']]
    reward_image_pos = [(x['X'], x['Y']) for x in info_dict['EVENT_DETAIL']]
    title_text = f'HAPPY\nBIRTHDAY\n{info_dict["CHARA_NAME_SHORT_EN"].upper()}!'
    subtitle_text = f'{info_dict['DATE'].month}/{info_dict['DATE'].day}'

    return gen_loginbonus_image(
        bg_name, card_image_files,
        reward_image_files, reward_quantities, reward_image_pos,
        title_text, subtitle_text,
        resource_path, ver
    )

def _master_login_event_row(info_dict: dict, login_event_id: int, year: int) -> dict:
    start_date = info_dict['DATE'].replace(year=year)
    end_date = start_date + timedelta(days=info_dict['DURATION_DAYS'])

    return {
        'ID': login_event_id,
        'NAME': info_dict['EVENT_NAME_JA'],
        'LIMIT_DAY': 0,  # limit to N days after first installation of game
        'START_YEAR': start_date.year,
        'START_MONTH': start_date.month,
        'START_DAY': start_date.day,
        'START_HOUR': 0,
        'START_MINUTE': 0,
        'END_YEAR': end_date.year,
        'END_MONTH': end_date.month,
        'END_DAY': end_date.day,
        'END_HOUR': 0,
        'END_MINUTE': 0
    }

def _master_login_event_detail(info_dict: dict) -> List[dict]:
    bg = f'login_event{info_dict["FIRST_ID"]}.png'
    message = f'Happy Birthday {info_dict["CHARA_NAME_SHORT_JA"]}！'

    out = deepcopy(LOGIN_EVENT_DETAIL)
    for row in out:
        row['BG'] = bg
        row['MESSAGE'] = message
    return out

def _gen_schedule_html_table(
        info_dicts: List[dict],
        strings: Dict[str, str],
        chara_name_key: str,
        indent: str='    '
    ) -> str:
    output = HTML_TABLE_STYLE + '\n'
    output += '<table class="loginbonus-schedule-birthday">\n'
    output += indent + '<tr>\n'
    output += indent*2 + f'<th>{strings.get("date")}</th>\n'
    output += indent*2 + f'<th>{strings.get("character_name")}</th>\n'
    output += indent*2 + f'<th>{strings.get("rewards")}</th>\n'
    output += indent + '</tr>\n'

    for info_dict in info_dicts:
        output += indent + '<tr>\n'

        date_str = info_dict['DATE'].strftime(strings.get('date_format'))
        date_cell = f'<td>{date_str}</td>'
        date_cell = indent*2 + date_cell + '\n'

        chara_str = info_dict[chara_name_key]
        chara_cell = f'<td>{chara_str}</td>'
        chara_cell = indent*2 + chara_cell + '\n'

        rewards_text = strings.get('n_jewels_for_d_days').format(n=EVENT_JEWELS_PER_DAY,
                                                                 d=info_dict['DURATION_DAYS'])
        rewards_cell = f'<td>{rewards_text}</td>'
        rewards_cell = indent*2 + rewards_cell + '\n'

        output += date_cell
        output += chara_cell
        output += rewards_cell
        output += indent + '</tr>\n'

    output += '</table>'
    return output

def _gen_markdown_page_en(info_dicts: List[dict]) -> str:
    output = '# Birthday Login Bonuses\n\n'
    output += 'Starting on members\' birthdays and lasting for five days, '
    output += 'login daily for free core jewels!\n\n'

    output += _gen_schedule_html_table(info_dicts, HTML_TABLE_STRINGS_EN, 'CHARA_NAME_EN')

    return output

def _gen_markdown_page_ja(info_dicts: List[dict]) -> str:
    output = '# 誕生日ログインボーナス\n\n'
    output += 'メンバーの誕生日に始まる、5日間の期限で毎日コアジュエルを手に入れる！\n\n'

    output += _gen_schedule_html_table(info_dicts, HTML_TABLE_STRINGS_JA, 'CHARA_NAME_JA')

    return output



def gen_loginbonus_birthday(resource_path, ver, start_year, end_year):
    master_login_event = read_json_decrypted(resource_path, ver, 'json/master_login_event.json')
    master_login_event = json.loads(master_login_event)
    master_login_event_detail_316 = read_json_decrypted(resource_path, ver, 'json/master_login_event_detail_316.json')
    master_login_event_detail_316 = json.loads(master_login_event_detail_316)

    login_event_id = max([row['ID'] for row in master_login_event[1:]]) + 1
    # go up to next multiple of 100, so it's neat
    login_event_id = math.ceil(login_event_id / 100) * 100
    first_login_event_id = login_event_id  # first occurence of each entry

    info_dicts = BIRTHDAY_BONUS_INFO
    for info_dict in info_dicts:
        info_dict['FIRST_ID'] = first_login_event_id
        info_dict['EVENT_DETAIL'] = _master_login_event_detail(info_dict)
        info_dict['IMAGE'] = _gen_bg_image(info_dict, resource_path, ver)
        info_dict['IMAGE'] = image_quantize(info_dict['IMAGE'])
        first_login_event_id += 1

    master_login_event_rows = []
    id_to_details = {}
    for year in range(start_year, end_year + 1):
        for info_dict in info_dicts:
            master_login_event_rows.append(_master_login_event_row(info_dict, login_event_id, year))
            id_to_details[login_event_id] = info_dict['EVENT_DETAIL']
            login_event_id += 1

    # print(master_login_event_rows)


    # output markdown pages
    md_en = _gen_markdown_page_en(info_dicts)
    with open(f'loginbonus_md/birthday.md', 'w', encoding='utf-8') as f:
        f.write(md_en)
    md_ja = _gen_markdown_page_ja(info_dicts)
    with open(f'loginbonus_md/birthday_ja.md', 'w', encoding='utf-8') as f:
        f.write(md_ja)


    # add event detail sheets
    replacements = {}
    for key, val in id_to_details.items():
        header_row = master_login_event_detail_316[0]
        full_table = [header_row] + val
        replacements[f'json/master_login_event_detail_{key}.json'] = json.dumps(full_table)
    replacements = encrypt_replacements_json(replacements)
    zip_path = path_join(resource_path, str(ver), '1_json01.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)


    # merge and replace master_login_event
    master_login_event.extend(master_login_event_rows)
    replacements = encrypt_replacements_json({
        'json/master_login_event.json': json.dumps(master_login_event)
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # add images
    replacements = {}
    for info_dict in info_dicts:
        io = BytesIO()
        info_dict['IMAGE'].save(io, format='PNG')
        first_id = info_dict['FIRST_ID']
        replacements[f'image/bg/login_event{first_id}.png'] = io.getvalue()
    zip_path = path_join(resource_path, str(ver), '1_bg.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 5:
        print('Usage: python gen_loginbonus_birthday.py <resource_path> <ver> <start_year> <end_year>')
        print('Example: python gen_loginbonus_birthday.py res 734 2026 2031')
        exit()

    gen_loginbonus_birthday(argv[1], int(argv[2]), int(argv[3]), int(argv[4]))
