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
from fractions import Fraction
import json
import math
import random
from typing import List, Tuple

from PIL import Image

from gacha_data.load_gacha_data import RARITY_ID_TO_NAME, load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, set_card_series_from_master_chara, \
    set_card_gacha_bg_from_master_chara, verify_gacha_data
from gen_gacha_banner_image import gen_gacha_banner_image
from gen_gacha_description_text import gen_gacha_description_text_combined
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

# note: game seems to use 32 bit math to do pulls (signed in some places),
# so this can be pretty large...  but keep it reasonable
PER_TOTAL_MAX = 1000000


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


def _gen_gacha_per_table(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict
    ):
    # Note: Gacha pulls are like a big spinner.
    #  - Each card takes up "per" segments of the spinner.
    #  - If it lands on the card, that's what you get.
    #  - For example, card 1 has per=1, card 2 has per=2, card 3 has per=3.
    #    Card 1 has a 1/6 chance. Card 2 has 2/6. Card 3 has 3/6.
    #    (6 equals 1+2+3, the total of all per values)
    #
    # So basically, this finds the probability of each individual card
    # (same for all of a given rarity and limited status), calculates a sutable total
    # number of segments that allows for exact (or approximated if too large) integer
    # number of segments per card, then scales card probabilities to reach that total.

    def per_card_probability(appearance_rate_pct: Decimal, num_cards: int) -> Fraction:
        if num_cards == 0:
            return Fraction(0, 1)
        p = Fraction(appearance_rate_pct / Decimal('100'))
        mult = Fraction(1, num_cards)
        return p * mult

    # returns per_val_exact, per_val_integer, error
    # (error is difference between exact and integer)
    def per_val_and_err(
            probability: Fraction,
            per_total: int
        ) -> Tuple[Fraction, int, Fraction]:
        p = probability
        per_exact = Fraction(p.numerator * per_total, p.denominator)
        assert(per_exact / per_total == p)
        per_int = int(per_exact)
        error = per_exact - per_int
        return per_exact, per_int, error

    lims_by_rarity = {}
    if limited_gacha_data_dict:
        for rarity_id in RARITY_ID_TO_NAME.keys():
            rarity_cards = [c for c in limited_gacha_data_dict.get('CARDS')
                            if c.rarity == rarity_id]
            if rarity_cards:
                lims_by_rarity[rarity_id] = {'cards': rarity_cards, 'p': 0}

    all_perm_cards = [c for series in permanent_gacha_data for c in series['CARDS']]
    perms_by_rarity = {}
    for rarity_id in RARITY_ID_TO_NAME.keys():
        rarity_cards = [c for c in all_perm_cards if c.rarity == rarity_id]
        if rarity_cards:
            perms_by_rarity[rarity_id] = {'cards': rarity_cards, 'p': 0}

    # find and gather probability per individual card of each type
    all_probabilities = []
    for rarity_id, rarity_name in RARITY_ID_TO_NAME.items():
        if lims_by_rarity.get(rarity_id):
            lim_rate = GACHA_ODDS.get(f'LIMITED_{rarity_name}', Decimal('0'))
            p = per_card_probability(lim_rate, len(lims_by_rarity[rarity_id]['cards']))
            lims_by_rarity[rarity_id]['p'] = p
            all_probabilities.append(p)
        else:
            lim_rate = Decimal('0')

        if perms_by_rarity.get(rarity_id):
            perm_rate = GACHA_ODDS.get(f'TOTAL_{rarity_name}', Decimal('0')) - lim_rate
            assert(perm_rate >= 0)
            p = per_card_probability(perm_rate, len(perms_by_rarity[rarity_id]['cards']))
            perms_by_rarity[rarity_id]['p'] = p
            all_probabilities.append(p)

    # try to find per value that can handle all cards exactly
    lcm = math.lcm(*[p.denominator for p in all_probabilities])
    # limit to a sane maximum though
    per_total = min(PER_TOTAL_MAX, lcm)

    table = []
    for entry in lims_by_rarity.values():
        per_exact, per_int, per_err = per_val_and_err(entry['p'], per_total)
        for card in entry['cards']:
            table.append({
                'card': card,
                'limited': True,
                'per_exact': per_exact,
                'per_int': per_int,
                'per_err': per_err
            })
    for entry in perms_by_rarity.values():
        per_exact, per_int, per_err = per_val_and_err(entry['p'], per_total)
        for card in entry['cards']:
            table.append({
                'card': card,
                'limited': False,
                'per_exact': per_exact,
                'per_int': per_int,
                'per_err': per_err
            })

    # verify math hasn't gone wrong
    sum_exacts = sum(e['per_exact'] for e in table)
    assert(sum_exacts == per_total)

    # if using an approximation, need to add a bit to calculated integer per values
    # to reach desired per_total.
    # do so by adding 1 to cards with highest error
    if per_total < lcm:
        # print(f'PER_TOTAL < LCM!!!, {per_total}, {lcm}')
        diff = per_total - sum(e['per_int'] for e in table)
        # note: shuffle cards so bias isn't introduced sequentially at start
        highest_errs = sorted(
            random.sample(table, k=len(table)),
            key=lambda x: x['per_err'],
            reverse=True
        )[:diff]
        for entry in highest_errs:
            entry['per_int'] += 1
            entry['per_err'] -= Fraction(1)

    # again, verify the math, but now on integers
    sum_ints = sum(e['per_int'] for e in table)
    assert(sum_ints == per_total)

    # reformat output a little for ergonomics
    # (specifically, just match game's format)
    output = [
        {
            'ID': e['card'].id,
            'PER': e['per_int'],
            'TOP': 1 if e['limited'] else 0,
            'BG': e['card'].gacha_bg,
            'MEMO': RARITY_ID_TO_NAME[e['card'].rarity]
        }
        for e in table
    ]
    return output


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

    per_table = _gen_gacha_per_table(permanent_gacha_data, None)
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

        per_table = _gen_gacha_per_table(permanent_gacha_data, banner)
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
