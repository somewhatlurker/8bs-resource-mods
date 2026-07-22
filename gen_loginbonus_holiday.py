# Generate login bonuses for holidays.

from copy import deepcopy
from datetime import date, timedelta
from io import BytesIO
import json
import math
from os.path import join as path_join
from typing import Dict, List

from PIL import Image

from loginbonus_common.gen_loginbonus_image import IMAGE_SAFE_AREA_SIZE, \
                                                   IMAGE_SAFE_AREA_MARGINS, \
                                                   gen_loginbonus_image
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


DEFAULT_EVENT_DAYS = 5
DEFAULT_EVENT_JEWEL_DAYS = 2
DEFAULT_EVENT_JEWEL_AMOUNT = 25

HOLIDAY_BONUS_INFO = [
    {
        'DATE': date(1970, 1, 1), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '元日', 'HOLIDAY_NAME_EN': 'New Year\'s Day',
        'EVENT_NAME_JA': 'HappyNewYear', 'EVENT_NAME_EN': 'Happy New Year',
        'BG': 'bg86', 'IMAGE_CARDS': (256, 243),  # Anri, Hotaru
        'BG_TITLE': 'HAPPY\nNEW YEAR', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 2, 2), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '節分', 'HOLIDAY_NAME_EN': 'Setsubun',
        'EVENT_NAME_JA': 'Setsubun', 'EVENT_NAME_EN': 'Setsubun',
        'BG': 'bg200', 'IMAGE_CARDS': (557, 558),  # Hinata, Suzune
        'BG_TITLE': 'SETSUBUN', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 2, 13), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': 'バレンタイン', 'HOLIDAY_NAME_EN': 'Valentine\'s Day',
        'EVENT_NAME_JA': 'HappyValentine', 'EVENT_NAME_EN': 'Happy Valentine\'s',
        'BG': 'bg120', 'IMAGE_CARDS': (261, 264),  # Suzune, Ayame
        'BG_TITLE': 'HAPPY\nVALENTINE\'S', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 3, 1), 'DURATION_DAYS': 31,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '春', 'HOLIDAY_NAME_EN': 'Spring',
        'EVENT_NAME_JA': '春ボーナス', 'EVENT_NAME_EN': 'Spring Bonus',
        'BG': 'bg144', 'IMAGE_CARDS': (342, 343),  # Hotaru, Mei
        'BG_TITLE': 'SPRING', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 3, 2), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': 'ひな祭り', 'HOLIDAY_NAME_EN': 'Dolls Day',
        'EVENT_NAME_JA': 'Hinamatsuri', 'EVENT_NAME_EN': 'Dolls Day',
        'BG': 'bg170', 'IMAGE_CARDS': (450, 453),  # Hinata, Hotaru
        'BG_TITLE': 'HINAMATSURI', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': 'easter', 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': 'イースター', 'HOLIDAY_NAME_EN': 'Easter',
        'EVENT_NAME_JA': 'HappyEaster', 'EVENT_NAME_EN': 'Happy Easter',
        'BG': 'bg242', 'IMAGE_CARDS': (768, 770),  # Yukina, Mei
        'BG_TITLE': 'HAPPY\nEASTER', 'BG_SHOW_SUBTITLE': False  # definitely don't show because date changes
    },
    {
        'DATE': date(1970, 4, 29), 'DURATION_DAYS': 7,
        'JEWEL_DAYS': 5,
        'JEWEL_AMOUNTS': [15] * 5,
        'HOLIDAY_NAME_JA': ' ゴールデンウィーク', 'HOLIDAY_NAME_EN': 'Golden Week',
        'EVENT_NAME_JA': 'GoldenWeek', 'EVENT_NAME_EN': 'Golden Week',
        'BG': 'bg128', 'IMAGE_CARDS': (572, 573),  # Ayame, Anri (Dreamland, because no good GW cards? lol)
        'BG_TITLE': 'GOLDEN\nWEEK', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 6, 1), 'DURATION_DAYS': 30,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '夏', 'HOLIDAY_NAME_EN': 'Summer',
        'EVENT_NAME_JA': '夏ボーナス', 'EVENT_NAME_EN': 'Summer Bonus',
        'BG': 'bg_live_52', 'IMAGE_CARDS': (507,),  # Yukina and Mei
        'BG_TITLE': 'SUMMER\nTIME', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 8, 1), 'DURATION_DAYS': 31,
        'JEWEL_DAYS': 8,
        'JEWEL_AMOUNTS': [10] * 7 + [18],
        'HOLIDAY_NAME_JA': 'エビストの月', 'HOLIDAY_NAME_EN': '8bs Month',
        'EVENT_NAME_JA': '8月はエビストの月', 'EVENT_NAME_EN': 'August is 8bs Month',
        'BG': 'bg243', 'IMAGE_CARDS': (564, 819, 668),  # Alumi, Hinata, Bellum
        'BG_TITLE': '8BS\nMONTH', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 8, 8), 'DURATION_DAYS': 1,
        'JEWEL_DAYS': 1,
        'JEWEL_AMOUNTS': [88],
        'HOLIDAY_NAME_JA': 'エビストの日', 'HOLIDAY_NAME_EN': '8bs Day',
        'EVENT_NAME_JA': '8月8日はエビストの日', 'EVENT_NAME_EN': 'August 8 is 8bs Day',
        'BG': 'bg243', 'IMAGE_CARDS': (667, 565, 821),  # Cwellan, Mint, Akari
        'BG_TITLE': '8BS\nDAY', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 9, 1), 'DURATION_DAYS': 30,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '秋', 'HOLIDAY_NAME_EN': 'Autumn',
        'EVENT_NAME_JA': '秋ボーナス', 'EVENT_NAME_EN': 'Autumn Bonus',
        'BG': 'bg85', 'IMAGE_CARDS': (628, 629),  # Alumi, Mint
        'BG_TITLE': 'AUTUMN', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 10, 28), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': 'ハロウィン', 'HOLIDAY_NAME_EN': 'Halloween',
        'EVENT_NAME_JA': 'HappyHalloween', 'EVENT_NAME_EN': 'Happy Halloween',
        'BG': 'bg155', 'IMAGE_CARDS': (384, 385),  # Hinata, Akari
        'BG_TITLE': 'HAPPY\nHALLOWEEN', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 12, 1), 'DURATION_DAYS': 31,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': '冬', 'HOLIDAY_NAME_EN': 'Winter',
        'EVENT_NAME_JA': '冬ボーナス', 'EVENT_NAME_EN': 'Winter Bonus',
        'BG': 'bg128', 'IMAGE_CARDS': (750,),  # Ayame and Anri
        'BG_TITLE': 'WINTER', 'BG_SHOW_SUBTITLE': False
    },
    {
        'DATE': date(1970, 12, 23), 'DURATION_DAYS': DEFAULT_EVENT_DAYS,
        'JEWEL_DAYS': DEFAULT_EVENT_JEWEL_DAYS,
        'JEWEL_AMOUNTS': [DEFAULT_EVENT_JEWEL_AMOUNT] * DEFAULT_EVENT_JEWEL_DAYS,
        'HOLIDAY_NAME_JA': 'クリスマス', 'HOLIDAY_NAME_EN': 'Christmas',
        'EVENT_NAME_JA': 'MerryChristmas', 'EVENT_NAME_EN': 'Merry Christmas',
        'BG': 'bg_live_15', 'IMAGE_CARDS': (418, 419),  # Suzune, Akari
        'BG_TITLE': 'MERRY\nCHRISTMAS', 'BG_SHOW_SUBTITLE': False
    }
]

EASTER_DATES = {
    2026: date(2026, 4, 5),
    2027: date(2027, 3, 28),
    2028: date(2028, 4, 16),
    2029: date(2029, 4, 1),
    2030: date(2030, 4, 21),
    2031: date(2031, 4, 13),
    2032: date(2032, 3, 28),
    2033: date(2033, 4, 17),
    2034: date(2034, 4, 9),
    2035: date(2035, 3, 25),
    2036: date(2036, 4, 13),
    2037: date(2037, 4, 5),
    2038: date(2038, 4, 25),
    2039: date(2039, 4, 10),
    2040: date(2040, 4, 1)
}

HTML_TABLE_STRINGS_JA = {
    'date': '日付',
    'date_format': '%m月%d日',
    'date_range_sep': '<wbr>〜<wbr>',
    'n_days_starting_day_before_easter': 'イースターの前日で始まる{n}日',
    'holiday': '祝日',
    'rewards': '報酬',
    'image': '画像',
    'day_number_d': 'ログイン{d}回目',
    'n_jewels': 'コアジュエル{n}個'
}
HTML_TABLE_STRINGS_EN = {
    'date': 'Date',
    'date_format': '%m/%d',
    'date_range_sep': '<wbr>〜<wbr>',
    'n_days_starting_day_before_easter': '{n} days starting the day before Easter',
    'holiday': 'Holiday',
    'rewards': 'Rewards',
    'image': 'Image',
    'day_number_d': 'Login {d}',
    'n_jewels': '{n} core jewels'
}

HTML_TABLE_STYLE = '''<style>
    table.loginbonus-schedule-holiday {
        border: 2px solid black;
        border-spacing: 0;
        margin: 0.5em 0;
    }
    table.loginbonus-schedule-holiday th, table.loginbonus-schedule-holiday td {
        border: 1px solid black;
        padding: 0.05em 0.25em;
    }
</style>'''

HTML_BANNER_IMAGE_PATH = '/static/loginbonus/login_event{id}.png'


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
    title_text = info_dict['BG_TITLE']

    if info_dict['BG_SHOW_SUBTITLE']:
        subtitle_text = f'{info_dict['DATE'].month}/{info_dict['DATE'].day}'
    else:
        subtitle_text = ''

    return gen_loginbonus_image(
        bg_name, card_image_files,
        reward_image_files, reward_quantities, reward_image_pos,
        title_text, subtitle_text,
        resource_path, ver
    )

def _event_start_date(info_dict: dict, year: int) -> date:
    start_date = info_dict['DATE']
    if isinstance(start_date, str):
        if start_date.lower() == 'easter':
            return EASTER_DATES[year] - timedelta(days=1)  # day before easter

    return start_date.replace(year=year)

def _master_login_event_row(info_dict: dict, login_event_id: int, year: int) -> dict:
    start_date = _event_start_date(info_dict, year)
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

def _master_login_event_detail_row(info_dict: dict, day: int) -> dict:
    # note: day is 0-indexed
    jewels = info_dict['JEWEL_AMOUNTS'][day]
    return {
        'ID': day + 1, 'DAY': day + 1, 'BG': f'login_event{info_dict["FIRST_ID"]}.png',
        'PAGE': 1, 'X': 70 + day * 120, 'Y': 67,
        'TITLE': f'コアジュエル × {jewels}', 'MESSAGE': info_dict['EVENT_NAME_JA'],
        'ITEM_TYPE': 0, 'ITEM_ID': 2, 'ITEM_NUM': jewels
    }

def _master_login_event_detail(info_dict: dict) -> List[dict]:
    return [
        _master_login_event_detail_row(info_dict, x)
        for x in range(info_dict['JEWEL_DAYS'])
    ]

def _gen_schedule_html_table(
        info_dicts: List[dict],
        strings: Dict[str, str],
        holiday_name_key: str,
        indent: str='    '
    ) -> str:
    output = HTML_TABLE_STYLE + '\n'
    output += '<table class="loginbonus-schedule-holiday">\n'
    output += indent + '<tr>\n'
    output += indent*2 + f'<th>{strings.get("date")}</th>\n'
    output += indent*2 + f'<th>{strings.get("holiday")}</th>\n'
    output += indent*2 + f'<th>{strings.get("rewards")}</th>\n'
    output += indent*2 + f'<th>{strings.get("image")}</th>\n'
    output += indent + '</tr>\n'

    for info_dict in info_dicts:
        output += indent + '<tr>\n'

        start_date = info_dict['DATE']
        if isinstance(start_date, str) and start_date.lower() == 'easter':
            date_str = strings.get('n_days_starting_day_before_easter').format(n=info_dict['DURATION_DAYS'])
        else:
            start_date = _event_start_date(info_dict, 1970)
            end_date = start_date + timedelta(days=info_dict['DURATION_DAYS'] - 1)
            start_date_str = start_date.strftime(strings.get('date_format'))
            end_date_str = end_date.strftime(strings.get('date_format'))
            date_str = start_date_str + strings.get('date_range_sep') + end_date_str
        date_cell = f'<td>{date_str}</td>'
        date_cell = indent*2 + date_cell + '\n'

        holiday_str = info_dict[holiday_name_key]
        holiday_cell = f'<td>{holiday_str}</td>'
        holiday_cell = indent*2 + holiday_cell + '\n'

        rewards_text = '\n' + indent*3 + '<ol>\n'
        for x in range(info_dict['JEWEL_DAYS']):
            rewards_text += indent*4 + '<li>'
            rewards_text += strings.get('day_number_d').format(d=x + 1) + ': '
            rewards_text += strings.get('n_jewels').format(n=info_dict['JEWEL_AMOUNTS'][x])
            rewards_text += '</li>\n'
        rewards_text += indent*3 + '</ol>\n' + indent*2

        rewards_cell = f'<td>{rewards_text}</td>'
        rewards_cell = indent*2 + rewards_cell + '\n'

        image_path = HTML_BANNER_IMAGE_PATH.format(id=info_dict['FIRST_ID'])
        image_tag = f'<img src="{image_path}" width=190 height=107 />'
        image_tag = indent*3 + image_tag + '\n'
        image_cell = indent*2 + '<td>\n' + image_tag + indent*2 + '</td>\n'

        output += date_cell
        output += holiday_cell
        output += rewards_cell
        output += image_cell
        output += indent + '</tr>\n'

    output += '</table>'
    return output

def _gen_markdown_page_en(info_dicts: List[dict]) -> str:
    output = '# Holiday Login Bonuses\n\n'
    output += 'Login during the holiday date periods to earn lots of core jewels!\n\n'

    output += _gen_schedule_html_table(info_dicts, HTML_TABLE_STRINGS_EN, 'HOLIDAY_NAME_EN')

    return output

def _gen_markdown_page_ja(info_dicts: List[dict]) -> str:
    output = '# 祝日ログインボーナス\n\n'
    output += '祝日の日付間隔にログインと、大量コアジュエルを手に入れられる！\n\n'

    output += _gen_schedule_html_table(info_dicts, HTML_TABLE_STRINGS_JA, 'HOLIDAY_NAME_JA')

    return output



def gen_loginbonus_holiday(resource_path, ver, start_year, end_year):
    master_login_event = read_json_decrypted(resource_path, ver, 'json/master_login_event.json')
    master_login_event = json.loads(master_login_event)
    master_login_event_detail_316 = read_json_decrypted(resource_path, ver, 'json/master_login_event_detail_316.json')
    master_login_event_detail_316 = json.loads(master_login_event_detail_316)

    login_event_id = max([row['ID'] for row in master_login_event[1:]]) + 1
    # go up to next multiple of 100, so it's neat
    login_event_id = math.ceil(login_event_id / 100) * 100
    first_login_event_id = login_event_id  # first occurence of each entry

    info_dicts = HOLIDAY_BONUS_INFO
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


    # output markdown pages and web images
    md_en = _gen_markdown_page_en(info_dicts)
    with open(f'loginbonus_md/holiday.md', 'w', encoding='utf-8') as f:
        f.write(md_en)
    md_ja = _gen_markdown_page_ja(info_dicts)
    with open(f'loginbonus_md/holiday_ja.md', 'w', encoding='utf-8') as f:
        f.write(md_ja)

    for info_dict in info_dicts:
        first_id = info_dict['FIRST_ID']
        # crop to safe area (to minimize wasted space in resized image)
        image = info_dict['IMAGE'].crop((
            IMAGE_SAFE_AREA_MARGINS[0],
            IMAGE_SAFE_AREA_MARGINS[1],
            IMAGE_SAFE_AREA_MARGINS[0] + IMAGE_SAFE_AREA_SIZE[0],
            IMAGE_SAFE_AREA_MARGINS[1] + IMAGE_SAFE_AREA_SIZE[1]
        ))
        # resize because no need for such large images on web
        image = image.convert('RGBA').resize((380, 214))
        image = image_quantize(image)
        image.save(f'loginbonus_md/static/loginbonus/login_event{first_id}.png')


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
        print('Usage: python gen_loginbonus_holiday.py <resource_path> <ver> <start_year> <end_year>')
        print('Example: python gen_loginbonus_holiday.py res 734 2026 2031')
        exit()

    gen_loginbonus_holiday(argv[1], int(argv[2]), int(argv[3]), int(argv[4]))
