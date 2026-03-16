# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from datetime import date
import json
import math
import random
from typing import List

from PIL import Image

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, set_card_series_from_master_chara, verify_gacha_data
from gen_gacha_banner_image import gen_gacha_banner_image
from util import read_json_decrypted


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'

# appearance rates in percent, total is rate including limited and permanent cards
GACHA_ODDS = {
    'LIMITED_UR': 1.2,  # game used around 0.6~1.2%
    'TOTAL_UR': 3.0,    # game used around 1.5~3.0%
    'LIMITED_SR': 2.0,  # game usually kept this a bit under 2%, but I like this
    'TOTAL_SR': 9.5,    # game usually used 8.5%, but sometimes 9.5%
    'LIMITED_R': 10.0   # should be unused, but put something here
}
# balance remainder to 100% with permanent R cards
GACHA_ODDS['TOTAL_R'] = 100 - GACHA_ODDS['TOTAL_UR'] - GACHA_ODDS['TOTAL_SR'] \
                      - GACHA_ODDS['LIMITED_R']

PERMANENT_DESCRIPTION_BANNER_TEXT = '「ステージ」「Anniversary」「ナイトメア」「B.A.C」などが登場!!'

ELEVEN_PULL_SR_GUARANTEE = True  # SR_SET


def gen_limited_gacha_banner_image_ja(
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


def gen_gacha_description_text_ja(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict
    ) -> str:
    if limited_gacha_data_dict:
        banner_text_raw = limited_gacha_data_dict.get('BANNER_TEXT_JA', '').strip()
        # remove newlines, balancing spaces around ampersands
        banner_text_raw = banner_text_raw.replace('\n& ', ' & ')
        banner_text_raw = banner_text_raw.replace(' &\n', ' & ')
        banner_text_raw = banner_text_raw.replace('\n', '')
        # remove spaces around ampersands
        banner_text_raw = banner_text_raw.replace('& ', '&')
        banner_text_raw = banner_text_raw.replace(' &', '&')

        banner_text = '<END_MONTH>月<END_DAY>日(<END_WEEKDAY_JA>)23:59まで\n'
        banner_text += '期間限定で' + banner_text_raw + 'が登場！'
    else:
        banner_text = PERMANENT_DESCRIPTION_BANNER_TEXT
    if ELEVEN_PULL_SR_GUARANTEE:
        banner_text += '\n11回ガチャでレア度SR以上が1枚以上確定！'
    banner_text += '\n\n'

    if limited_gacha_data_dict:
        all_cards = limited_gacha_data_dict['CARDS']
        has_limited_ur = len([c for c in all_cards if c.rarity == 4]) > 0
        has_limited_sr = len([c for c in all_cards if c.rarity == 3]) > 0
        has_limited_r = len([c for c in all_cards if c.rarity == 2]) > 0
    else:
        has_limited_ur = False
        has_limited_sr = False
        has_limited_r = False

    odds_text = '<レアリティ別提供割合>\n'
    odds_text += f'UR[★★★★]：{GACHA_ODDS['TOTAL_UR']:.1f}%\n'
    if has_limited_ur:
        lim_percent = GACHA_ODDS['LIMITED_UR']
        perm_percent = GACHA_ODDS['TOTAL_UR'] - lim_percent
        odds_text += f'(内訳：期間限定{lim_percent:.1f}% 通常{perm_percent:.1f}%)\n'
    odds_text += f'SR[★★★]：{GACHA_ODDS['TOTAL_SR']:.1f}%\n'
    if has_limited_sr:
        lim_percent = GACHA_ODDS['LIMITED_SR']
        perm_percent = GACHA_ODDS['TOTAL_SR'] - lim_percent
        odds_text += f'(内訳：期間限定{lim_percent:.1f}% 通常{perm_percent:.1f}%)\n'
    odds_text += f'SR[★★★]：{GACHA_ODDS['TOTAL_R']:.1f}%\n'
    if has_limited_r:
        lim_percent = GACHA_ODDS['LIMITED_R']
        perm_percent = GACHA_ODDS['TOTAL_R'] - lim_percent
        odds_text += f'(内訳：期間限定{lim_percent:.1f}% 通常{perm_percent:.1f}%)\n'
    odds_text += '\n'

    contents_text = '<ガチャ内容>\n'
    contents_text += 'UR[★★★★]\n'
    if limited_gacha_data_dict:
        lim_desc_text = limited_gacha_data_dict.get('UR_DESC_TEXT_JA', '').strip()
        if lim_desc_text:
            contents_text += '期間限定:\n' + lim_desc_text + '\n通常:\n'
    for series in permanent_gacha_data:
        perm_desc_text = series.get('UR_DESC_TEXT_JA', '').strip()
        if perm_desc_text:
            contents_text += perm_desc_text + '\n'
    contents_text += '\nSR[★★★★]\n'
    if limited_gacha_data_dict:
        lim_desc_text = limited_gacha_data_dict.get('SR_DESC_TEXT_JA', '').strip()
        if lim_desc_text:
            contents_text += '期間限定:\n' + lim_desc_text + '\n通常:\n'
    for series in permanent_gacha_data:
        perm_desc_text = series.get('SR_DESC_TEXT_JA', '').strip()
        if perm_desc_text:
            contents_text += perm_desc_text + '\n'
    contents_text += '\nR[★★★★]\n'
    if limited_gacha_data_dict:
        lim_desc_text = limited_gacha_data_dict.get('R_DESC_TEXT_JA', '').strip()
        if lim_desc_text:
            contents_text += '期間限定:\n' + lim_desc_text + '\n通常:\n'
    for series in permanent_gacha_data:
        perm_desc_text = series.get('R_DESC_TEXT_JA', '').strip()
        if perm_desc_text:
            contents_text += perm_desc_text + '\n'
    contents_text += '\n'

    footer_text = '・一部のメンバーはカード情報ボタンで初期ステータスを確認できます。\n'
    footer_text += '・期間限定で出るメンバーは、再度期間限定で登場する場合があります。'

    return banner_text + odds_text + contents_text + footer_text


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

    verify_gacha_data(limited_gacha_data, permanent_gacha_data,
                      master_chara, master_series)

    gacha_id = max([row['ID'] for row in master_gacha_main[1:]]) + 1
    # go up to next multiple of 1000, so it's neat
    gacha_id = math.ceil(gacha_id / 1000) * 1000

    perm_banner_image = gen_gacha_banner_image(None, [], 'プレミアム', None, resource_path,
                                               ver)
    perm_banner_image = perm_banner_image.convert('RGB').quantize()
    perm_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')
    gacha_id += 1

    for banner in limited_gacha_data:
        lim_banner_image = gen_limited_gacha_banner_image_ja(banner, gacha_id,
                                                            resource_path, ver)
        lim_banner_image = lim_banner_image.convert('RGB').quantize()
        lim_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')

        desc_text = gen_gacha_description_text_ja(permanent_gacha_data, banner)
        with open(f'gacha_banners/banner{gacha_id}.txt', 'w', encoding='utf-8') as f:
            f.write(desc_text)

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
