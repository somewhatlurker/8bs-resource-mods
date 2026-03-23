# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from datetime import date
from decimal import Decimal
import json
import math
import random

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
        limited_gacha_data_dict: dict,
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

    perm_banner_image = gen_gacha_banner_image(None, [], 'プレミアム', None, resource_path,
                                               ver)
    perm_banner_image = perm_banner_image.convert('RGB').quantize()
    perm_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')

    perm_desc_text = gen_gacha_description_text_combined(permanent_gacha_data, None,
                                                         GACHA_ODDS,
                                                         ELEVEN_PULL_SR_GUARANTEE)
    with open(f'gacha_banners/banner{gacha_id}.txt', 'w', encoding='utf-8') as f:
        f.write(perm_desc_text)

    per_table = gen_gacha_per_table(permanent_gacha_data, None, GACHA_ODDS)
    with open(f'gacha_banners/table{gacha_id}.txt', 'w', encoding='utf-8') as f:
        json.dump(per_table, f)

    gacha_id += 1

    for banner in limited_gacha_data:
        lim_banner_image = _gen_limited_gacha_banner_image_ja(banner, gacha_id,
                                                              resource_path, ver)
        lim_banner_image = lim_banner_image.convert('RGB').quantize()
        lim_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')

        lim_desc_text = gen_gacha_description_text_combined(permanent_gacha_data, banner,
                                                            GACHA_ODDS,
                                                            ELEVEN_PULL_SR_GUARANTEE)
        with open(f'gacha_banners/banner{gacha_id}.txt', 'w', encoding='utf-8') as f:
            f.write(lim_desc_text)

        per_table = gen_gacha_per_table(permanent_gacha_data, banner, GACHA_ODDS)
        with open(f'gacha_banners/table{gacha_id}.txt', 'w', encoding='utf-8') as f:
            json.dump(per_table, f)

        gacha_id += 1

    # print(limited_gacha_data)
    # print(permanent_gacha_data)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver>')
        print('Example: python gen_gacha_rotation.py res 733')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]))
