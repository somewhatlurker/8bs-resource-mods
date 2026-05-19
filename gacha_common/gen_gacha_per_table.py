from decimal import Decimal
from fractions import Fraction
import math
import random
from typing import List, Tuple

from .gacha_data.load_gacha_data import RARITY_ID_TO_NAME


# note: game seems to use 32 bit math to do pulls (signed in some places),
# so this can be pretty large (theoretically max s32 int)...  but keep it reasonable
# (especially important because step-up gacha may inflate the total)
PER_TOTAL_MAX = 1000000


def gen_gacha_stepup_per_table(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict,
        appearance_rates: dict
    ):
    """Generate the rates detail sheet ("per" table) for a step-up gacha series.

    - permanent_gacha_data is in the format returned by
        gacha_data.load_gacha_data.load_and_parse_gacha_data_csv
    - limited_gacha_data_dict is a single element from the format returned by
        gacha_data.load_gacha_data.load_and_parse_gacha_data_csv
    - appearance_rates should be a dictionary of str to Decimal, with the following keys:
        - LIMITED_UR
        - TOTAL_UR
        - LIMITED_SR
        - TOTAL_SR
        - LIMITED_R
        - TOTAL_R
        (values are percentage chance -- e.g. 2.0 == 2.0%)

    All of the limited cards will be made into pickup cards.

    Call gacha_data.load_gacha_data.set_card_gacha_bg_from_master_chara on data first if
    BG field needs to be set.
    """
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
            lim_rate = appearance_rates.get(f'LIMITED_{rarity_name}', Decimal('0'))
            p = per_card_probability(lim_rate, len(lims_by_rarity[rarity_id]['cards']))
            lims_by_rarity[rarity_id]['p'] = p
            all_probabilities.append(p)
        else:
            lim_rate = Decimal('0')

        if perms_by_rarity.get(rarity_id):
            total_rate = appearance_rates.get(f'TOTAL_{rarity_name}', Decimal('0'))
            perm_rate = total_rate - lim_rate
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
            'BG': e['card'].gacha_bg if e['card'].gacha_bg else 0,
            'RARE': e['card'].rarity,
            'PICKUP': 1 if e['limited'] else 0,
            'MEMO': RARITY_ID_TO_NAME[e['card'].rarity]
        }
        for e in table
    ]
    return output

def gen_gacha_per_table(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict,
        appearance_rates: dict
    ):
    """Generate the rates detail sheet ("per" table) for a gacha series.

    - permanent_gacha_data is in the format returned by
        gacha_data.load_gacha_data.load_and_parse_gacha_data_csv
    - limited_gacha_data_dict is a single element from the format returned by
        gacha_data.load_gacha_data.load_and_parse_gacha_data_csv
    - appearance_rates should be a dictionary of str to Decimal, with the following keys:
        - LIMITED_UR
        - TOTAL_UR
        - LIMITED_SR
        - TOTAL_SR
        - LIMITED_R
        - TOTAL_R
        (values are percentage chance -- e.g. 2.0 == 2.0%)

    Call gacha_data.load_gacha_data.set_card_gacha_bg_from_master_chara on data first if
    BG field needs to be set.
    """
    # This is same as for stepup gacha, but with some fields removed.
    table = gen_gacha_stepup_per_table(permanent_gacha_data, limited_gacha_data_dict,
                                       appearance_rates)
    for row in table:
        del row['RARE']
        del row['PICKUP']
    return table
