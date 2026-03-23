# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from datetime import date, timedelta
from decimal import Decimal
import json
import math
import random
from typing import List

from PIL import Image

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, set_card_series_from_master_chara, \
    set_card_gacha_bg_from_master_chara, verify_gacha_data
from gen_gacha_banner_image import gen_gacha_banner_image
from gen_gacha_description_text import gen_gacha_description_text_combined
from gen_gacha_per_table import gen_gacha_per_table
from util import read_json_decrypted


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'

# appearance rates in percent, total is rate including limited and permanent cards
GACHA_ODDS = {
    'LIMITED_UR': Decimal('1.2'),  # game used around 0.6~1.2%
    'TOTAL_UR': Decimal('3.0'),    # game used around 1.5~3.0%
    'LIMITED_SR': Decimal('2.0'),  # game usually kept it a bit under 2%, but I like this
    'TOTAL_SR': Decimal('9.5'),    # game usually used 8.5%, but sometimes 9.5%
    'LIMITED_R': Decimal('10.0')   # should be unused, but put something here
}
# balance remainder to 100% with permanent R cards
GACHA_ODDS['TOTAL_R'] = Decimal('100') - GACHA_ODDS['TOTAL_UR'] - GACHA_ODDS['TOTAL_SR']

ELEVEN_PULL_SR_GUARANTEE = True  # SR_SET


def _gen_limited_gacha_banner_image_ja(
        limited_gacha_data_dict: dict | None,
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    if limited_gacha_data_dict:
        bg_name = limited_gacha_data_dict.get('BANNER_BG')
        image_cards = [c for c in limited_gacha_data_dict['CARDS'] if c.rarity == 4]
        description_text = limited_gacha_data_dict.get('BANNER_TEXT_JA')
    else:
        bg_name = None
        image_cards = []
        description_text = None

    is_single_chara_banner = len(set([c.chara for c in image_cards])) == 1

    if len(image_cards) and hasattr(image_cards[0], 'series'):
        # split series up into separate lists so they're easier to keep track of
        image_card_series = {}
        for c in image_cards:
            if c.series in image_card_series:
                image_card_series[c.series].append(c)
            else:
                image_card_series[c.series] = [c]
        image_card_series = [v for v in image_card_series.values()]

        # randomly select up to four cards, max of one for each character in the banner
        # round robin between series to ensure roughly fair representation
        shuffled_image_cards = []
        rd = random.Random(output_gacha_id)
        series_idx = 0
        for _ in range(4):
            series_idx = (series_idx + 1) % len(image_card_series)
            series = image_card_series[series_idx]
            if len(series) == 0: continue

            card_idx = rd.randrange(len(series))
            card = series[card_idx]
            shuffled_image_cards.append(card.id)
            if is_single_chara_banner:
                # remove only the single card
                del series[card_idx]
            else:
                # remove all cards with same chara ID from all series
                # to prevent them from being chosen
                for i in range(len(image_card_series)):
                    s = image_card_series[i]
                    image_card_series[i] = [c for c in s if c.chara != card.chara]

            # break loop if no remaining cards in any series
            card_count = sum([len(s) for s in image_card_series])
            if card_count == 0: break
    else:
        # randomly select up to four cards, max of one for each character in the banner
        # (fallback for no series data)
        shuffled_image_cards = []
        rd = random.Random(output_gacha_id)
        for _ in range(4):
            if len(image_cards) == 0: break
            idx = rd.randrange(len(image_cards))
            card = image_cards[idx]
            shuffled_image_cards.append(card.id)
            if is_single_chara_banner:
                # remove only the single card
                del image_cards[idx]
            else:
                # remove all cards with same chara ID to prevent them from being chosen
                image_cards = [c for c in image_cards if c.chara != card.chara]

    return gen_gacha_banner_image(
        bg_name,
        [f'image/chara/stand/stand_chara{id}_2.png' for id in shuffled_image_cards],
        'プレミアム',
        description_text,
        resource_path,
        ver
    )


def _gacha_list_entry(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        first_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> dict:
    banner_image = _gen_limited_gacha_banner_image_ja(limited_gacha_data_dict,
                                                      first_gacha_id, resource_path, ver)
    banner_image = banner_image.convert('RGB').quantize()
    # banner_image.save(f'gacha_banners/img_banner{first_gacha_id}.png')

    desc_text = gen_gacha_description_text_combined(permanent_gacha_data,
                                                    limited_gacha_data_dict, GACHA_ODDS,
                                                    ELEVEN_PULL_SR_GUARANTEE)
    # with open(f'gacha_banners/banner{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     f.write(desc_text)

    per_table = gen_gacha_per_table(permanent_gacha_data, limited_gacha_data_dict,
                                    GACHA_ODDS)
    # with open(f'gacha_banners/table{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     json.dump(per_table, f)

    print(f'Gacha entry generated, id={first_gacha_id}')

    return {
        'first_gacha_id': first_gacha_id,
        'banner_image': banner_image,
        'desc_text': desc_text,
        'per_table': per_table,
        'limited_data': limited_gacha_data_dict
    }

def _master_gacha_row(entry: dict, gacha_id: int, year: int) -> dict:
    limited_data = entry.get('limited_data')
    if limited_data:
        iso_week = limited_data['ISO_WEEK']
        duration = limited_data['DURATION_DAYS']
        date_offset = limited_data.get('DATE_OFFSET', 0)

        start_date = date.fromisocalendar(year, iso_week, date_offset + 1)
        # note: end_date is day *after* end, not day of end
        end_date = start_date + timedelta(days=date_offset)
    else:
        start_date = None
        end_date = None

    weekdays_ja = {
        0: '月',
        1: '火',
        2: '水',
        3: '木',
        4: '金',
        5: '土',
        6: '日'
    }
    weekdays_en = {
        0: 'Mon',
        1: 'Tue',
        2: 'Wed',
        3: 'Thu',
        4: 'Fri',
        5: 'Sat',
        6: 'Sun'
    }

    desc_text = entry['desc_text'].replace('\n', '$')
    if start_date:
        desc_text = desc_text.replace('<START_MONTH>', str(start_date.month))
        desc_text = desc_text.replace('<START_DAY>', str(start_date.day))
        weekday = start_date.weekday()
        desc_text = desc_text.replace('<START_WEEKDAY_JA>', weekdays_ja.get(weekday))
        desc_text = desc_text.replace('<START_WEEKDAY_EN>', weekdays_en.get(weekday))
    if end_date:
        # description text says until 11:59 of day before end date in date
        desc_end_date = end_date - timedelta(days=1)
        desc_text = desc_text.replace('<END_MONTH>', str(desc_end_date.month))
        desc_text = desc_text.replace('<END_DAY>', str(desc_end_date.day))
        weekday = desc_end_date.weekday()
        desc_text = desc_text.replace('<END_WEEKDAY_JA>', weekdays_ja.get(weekday))
        desc_text = desc_text.replace('<END_WEEKDAY_EN>', weekdays_en.get(weekday))

    return {
        'ID': gacha_id,
        'GACHA_TYPE': 0,  # regular premium gacha
        'NAME': 'プレミアムガチャ',
        'ORDER': 1,  # seems to be based on type
        'BANNER': f'img_banner{entry["first_gacha_id"]}',
        'DETAIL': desc_text,
        'USE_ITEM': 2,  # jewels
        'GACHA_1': 25,  # don't chang costs -- image assets have value hardcoded
        'GACHA_10': 0,
        'GACHA_11': 250,
        'SR_SET': 1 if ELEVEN_PULL_SR_GUARANTEE else 0,
        'SHEET': f'gacha_detail{entry["first_gacha_id"]}',
        'SHEET_DAILY': f'gacha_detail{entry["first_gacha_id"]}',  # just reuse same sheet
        'FROM_INSTALL': 0,
        'START_YEAR': start_date.year if start_date else 0,
        'START_MONTH': start_date.month if start_date else 0,
        'START_DAY': start_date.day if start_date else 0,
        'START_HOUR': 0,
        'START_MINUTE': 0,
        'END_YEAR': end_date.year if end_date else 0,
        'END_MONTH': end_date.month if end_date else 0,
        'END_DAY': end_date.day if end_date else 0,
        'END_HOUR': 0,
        'END_MINUTE': 0
    }


def gen_gacha_rotation(resource_path, ver):
    master_chara = read_json_decrypted(resource_path, ver, 'json/master_chara.json')
    master_chara = json.loads(master_chara)
    master_gacha_main = read_json_decrypted(resource_path, ver, 'json/master_gacha_main.json')
    master_gacha_main = json.loads(master_gacha_main)
    master_series = read_json_decrypted(resource_path, ver, 'json/master_series.json')
    master_series = json.loads(master_series)

    limited_gacha_data = load_and_parse_gacha_data_csv(LIMITED_CSV_PATH)
    permanent_gacha_data = load_and_parse_gacha_data_csv(PERMANENT_CSV_PATH)

    set_card_names_from_master_chara(limited_gacha_data, master_chara)
    set_card_names_from_master_chara(permanent_gacha_data, master_chara)
    set_card_series_from_master_chara(limited_gacha_data, master_chara)
    set_card_series_from_master_chara(permanent_gacha_data, master_chara)
    set_card_gacha_bg_from_master_chara(limited_gacha_data, master_chara)
    set_card_gacha_bg_from_master_chara(permanent_gacha_data, master_chara)

    verify_gacha_data(limited_gacha_data, permanent_gacha_data,
                      master_chara, master_series)

    gacha_id = max([row['ID'] for row in master_gacha_main[1:]]) + 1
    # go up to next multiple of 1000, so it's neat
    gacha_id = math.ceil(gacha_id / 1000) * 1000
    first_gacha_id = gacha_id  # first occurence of each entry

    permanent_gacha_entry = _gacha_list_entry(permanent_gacha_data, None, first_gacha_id,
                                              resource_path, ver)
    first_gacha_id += 1

    limited_gacha_unique_entires = []
    for banner in limited_gacha_data:
        entry = _gacha_list_entry(permanent_gacha_data, banner, first_gacha_id,
                                  resource_path, ver)
        limited_gacha_unique_entires.append(entry)
        first_gacha_id += 1

    # print(permanent_gacha_entry)
    # print(limited_gacha_unique_entires)

    master_gacha_rows = []
    master_gacha_rows.append(_master_gacha_row(permanent_gacha_entry, first_gacha_id, 2025))
    first_gacha_id += 1

    for year in range(2025, 2038):
        for entry in limited_gacha_unique_entires:
            master_gacha_rows.append(_master_gacha_row(entry, first_gacha_id, year))
            first_gacha_id += 1

    print(master_gacha_rows)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver>')
        print('Example: python gen_gacha_rotation.py res 733')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]))
