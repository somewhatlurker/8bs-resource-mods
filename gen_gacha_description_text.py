from typing import List

from gacha_data.load_gacha_data import RARITY_NAME_TO_ID

PERMANENT_DESCRIPTION_BANNER_TEXT_JA = '「ステージ」「Anniversary」「ナイトメア」「B.A.C」などが登場!!'
PERMANENT_DESCRIPTION_BANNER_TEXT_EN = '[Stage] [Anniversary] [Nightmare] [B.A.C] and more are available!!'

# matches with ID, but semantically different so define again
RARITY_TO_STARS = {
    'N': 1,
    'R': 2,
    'SR': 3,
    'UR': 4
}


def _gacha_description_banner_text_ja(
        limited_gacha_data_dict: dict,
        sr_guarantee: bool
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

        start_date_text = '<START_MONTH>月<START_DAY>日(<START_WEEKDAY_JA>)00:00'
        end_date_text = '<END_MONTH>月<END_DAY>日(<END_WEEKDAY_JA>)23:59'
        banner_text = f'{start_date_text}〜{end_date_text}まで\n'
        banner_text += f'期間限定で{banner_text_raw}が登場！'
    else:
        banner_text = PERMANENT_DESCRIPTION_BANNER_TEXT_JA

    if sr_guarantee:
        banner_text += '\n11回ガチャでレア度SR以上が1枚以上確定！'

    banner_text += '\n\n'
    return banner_text

def _gacha_description_banner_text_en(
        limited_gacha_data_dict: dict,
        sr_guarantee: bool
    ) -> str:
    if limited_gacha_data_dict:
        banner_text_raw = limited_gacha_data_dict.get('BANNER_TEXT_EN', '').strip()
        # remove newlines, inserting space at line break
        banner_text_raw = banner_text_raw.replace('\n', ' ')

        start_date_text = '00:00 <START_MONTH>/<START_DAY> (<START_WEEKDAY_EN>)'
        end_date_text = '23:59 <END_MONTH>/<END_DAY> (<END_WEEKDAY_EN>)'
        banner_text = f'For a limited time during {start_date_text}~{end_date_text},\n'
        banner_text += f'{banner_text_raw} will appear in gacha!'
    else:
        banner_text = PERMANENT_DESCRIPTION_BANNER_TEXT_EN

    if sr_guarantee:
        banner_text += '\nAt least one SR or better card is guaranteed in 11-times gacha!'

    banner_text += '\n\n'
    return banner_text


def _gacha_description_odds_text_internal(
        limited_gacha_data_dict: dict,
        appearance_rates: dict,
        heading: str,
        lim_perm_fmt: str
    ):
    def odds_string_for_rarity(rarity: str):
        rarity = rarity.upper()
        total_key = f'TOTAL_{rarity}'
        limited_key = f'LIMITED_{rarity}'

        if appearance_rates.get(total_key, 0) == 0:
            return ''

        rarity_id = RARITY_NAME_TO_ID[rarity]
        if limited_gacha_data_dict:
            all_lim_cards = limited_gacha_data_dict['CARDS']
            rarity_lim_cards = [c for c in all_lim_cards if c.rarity == rarity_id]
            has_limited = len(rarity_lim_cards) > 0
        else:
            has_limited = False

        text = f'{rarity}[{"★" * RARITY_TO_STARS[rarity]}]：{appearance_rates[total_key]}%\n'
        if has_limited:
            lim_pct = appearance_rates.get(limited_key, 0)
            perm_pct = appearance_rates[total_key] - lim_pct
            text += lim_perm_fmt.format(lim_percent=lim_pct, perm_percent=perm_pct)
            text += '\n'
        return text

    odds_text = f'{heading}\n'
    odds_text += odds_string_for_rarity('UR')
    odds_text += odds_string_for_rarity('SR')
    odds_text += odds_string_for_rarity('R')
    odds_text += odds_string_for_rarity('N')
    odds_text += '\n'
    return odds_text

def _gacha_description_odds_text_ja(
        limited_gacha_data_dict: dict,
        appearance_rates: dict
    ):
    return _gacha_description_odds_text_internal(
        limited_gacha_data_dict,
        appearance_rates,
        '<レアリティ別提供割合>',
        '(内訳：期間限定{lim_percent}% 通常{perm_percent}%)'
    )

def _gacha_description_odds_text_en(
        limited_gacha_data_dict: dict,
        appearance_rates: dict
    ):
    return _gacha_description_odds_text_internal(
        limited_gacha_data_dict,
        appearance_rates,
        '<Appearance Rates>',
        '(Limited cards: {lim_percent}%, Permanent cards: {perm_percent}%)'
    )


def _gacha_description_contents_text_internal(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        appearance_rates: dict,
        lang_code: str,
        main_heading: str,
        lim_subheading: str,
        perm_subheading: str
    ):
    lang_code = lang_code.upper()

    def contents_string_for_rarity(rarity: str):
        rarity = rarity.upper()
        desc_text_key = f'{rarity}_DESC_TEXT_{lang_code}'
        total_key = f'TOTAL_{rarity}'

        if appearance_rates.get(total_key, 0) == 0:
            return ''

        text = ''

        if limited_gacha_data_dict:
            lim_desc_text = limited_gacha_data_dict.get(desc_text_key, '').strip()
            if lim_desc_text:
                text += f'{lim_subheading}\n' + lim_desc_text + f'\n{perm_subheading}\n'

        for series in permanent_gacha_data:
            perm_desc_text = series.get(desc_text_key, '').strip()
            if perm_desc_text:
                text += perm_desc_text + '\n'

        if not text:
            return ''

        text = f'{rarity}[{"★" * RARITY_TO_STARS[rarity]}]\n' + text + '\n'
        return text

    contents_text = f'{main_heading}\n'
    contents_text += contents_string_for_rarity('UR')
    contents_text += contents_string_for_rarity('SR')
    contents_text += contents_string_for_rarity('R')
    contents_text += contents_string_for_rarity('N')
    return contents_text

def _gacha_description_contents_text_ja(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        appearance_rates: dict
    ) -> str:
    return _gacha_description_contents_text_internal(
        permanent_gacha_data,
        limited_gacha_data_dict,
        appearance_rates,
        'JA',
        '<ガチャ内容>',
        '期間限定:',
        '通常:'
    )

def _gacha_description_contents_text_en(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        appearance_rates: dict
    ) -> str:
    return _gacha_description_contents_text_internal(
        permanent_gacha_data,
        limited_gacha_data_dict,
        appearance_rates,
        'EN',
        '<Gacha Contents>',
        'Limited cards:',
        'Permanent cards:'
    )


def gen_gacha_description_text_ja(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict,
        appearance_rates: dict,
        sr_guarantee: bool
    ) -> str:
    """Generate English gacha description text.

    - appearance_rates should be a dictionary of str to Decimal, with the following keys:
        - LIMITED_UR
        - TOTAL_UR
        - LIMITED_SR
        - TOTAL_SR
        - LIMITED_R
        - TOTAL_R
        (values are percentage chance -- e.g. 2.0 == 2.0%)
    - sr_guarantee is whether or not an SR or better card is guaranteed in an 11-pull
    """
    banner_text = _gacha_description_banner_text_ja(limited_gacha_data_dict, sr_guarantee)
    odds_text = _gacha_description_odds_text_ja(limited_gacha_data_dict, appearance_rates)
    contents_text = _gacha_description_contents_text_ja(permanent_gacha_data,
                                                        limited_gacha_data_dict,
                                                        appearance_rates)
    footer_text = '・一部のメンバーはカード情報ボタンで初期ステータスを確認できます。\n'
    footer_text += '・期間限定で出るメンバーは、再度期間限定で登場する場合があります。'
    return banner_text + odds_text + contents_text + footer_text

def gen_gacha_description_text_en(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict,
        appearance_rates: dict,
        sr_guarantee: bool
    ) -> str:
    """Generate English gacha description text.

    - appearance_rates should be a dictionary of str to Decimal, with the following keys:
        - LIMITED_UR
        - TOTAL_UR
        - LIMITED_SR
        - TOTAL_SR
        - LIMITED_R
        - TOTAL_R
        (values are percentage chance -- e.g. 2.0 == 2.0%)
    - sr_guarantee is whether or not an SR or better card is guaranteed in an 11-pull
    """
    banner_text = _gacha_description_banner_text_en(limited_gacha_data_dict, sr_guarantee)
    odds_text = _gacha_description_odds_text_en(limited_gacha_data_dict, appearance_rates)
    contents_text = _gacha_description_contents_text_en(permanent_gacha_data,
                                                        limited_gacha_data_dict,
                                                        appearance_rates)
    footer_text = '・You can see the initial stats of some cards by tapping the card information button.\n'
    footer_text += '・Limited cards may be re-released in the future.'
    return banner_text + odds_text + contents_text + footer_text

def gen_gacha_description_text_combined(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict,
        appearance_rates: dict,
        sr_guarantee: bool
    ) -> str:
    """Generate combined gacha description text (Japanese and English).

    - appearance_rates should be a dictionary of str to Decimal, with the following keys:
        - LIMITED_UR
        - TOTAL_UR
        - LIMITED_SR
        - TOTAL_SR
        - LIMITED_R
        - TOTAL_R
        (values are percentage chance -- e.g. 2.0 == 2.0%)
    - sr_guarantee is whether or not an SR or better card is guaranteed in an 11-pull
    """
    text = 'SCROLL DOWN FOR ENGLISH!\n\n'
    text += gen_gacha_description_text_ja(permanent_gacha_data, limited_gacha_data_dict,
                                          appearance_rates, sr_guarantee)
    text += '\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n'
    text += gen_gacha_description_text_en(permanent_gacha_data, limited_gacha_data_dict,
                                          appearance_rates, sr_guarantee)
    return text
