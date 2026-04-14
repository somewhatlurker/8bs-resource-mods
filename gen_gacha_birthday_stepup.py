# Generate birthday gacha banners in step-up gacha.
# The banner contains only the birthday girl's cards for SR and UR rarities
# (including event cards).
# R rarity includes the same cards as permanent gacha.
# Birthday cards are used as pickup where available, otherwise all UR cards are.

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
import json
import math
from os.path import join as path_join
import random
from typing import Dict, List

from PIL import Image

from gacha_common.gacha_data.load_gacha_data import CardDetail, \
    load_and_parse_gacha_data_csv, set_card_names_from_master_chara, \
    set_card_series_from_master_chara, set_card_gacha_bg_from_master_chara
from gacha_common.gen_stepup_gacha_banner_image import gen_stepup_gacha_banner_image
from gacha_common.gen_gacha_description_text import \
    gen_gacha_stepup_description_text_combined
from gacha_common.gen_gacha_per_table import gen_gacha_stepup_per_table
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


PERMANENT_CSV_PATH = 'gacha_common/gacha_data/permanent.csv'

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

BIRTHDAY_BANNERS = [
    {
        'DATE': date(1900, 1, 11),
        'NAME_JA': 'B.A.Cメンバー', 'NAME_EN': 'B.A.C Members\'',
        'NAME_SHORT_JA': 'B.A.C', 'NAME_SHORT_EN': 'B.A.C',
        'DESC_JA': 'SR以上はB.A.Cメンバーのみ出現！',
        'DESC_EN': 'SR and above are B.A.C members only!',
        'BG': 'bg222',
        'CHARAS': (13, 14, 15)
    }
]
# Add all of 8/pLanet!!, and 2_wEi (sorted by birthday)
# No Kanade due to lack of cards
for chara_id in (7, 4, 5, 3, 2, 8, 6, 11, 12, 1):
    BIRTHDAY_BANNERS.append({
        'DATE': CHARA_BIRTHDAYS[chara_id],
        'NAME_JA': CHARA_NAMES_JA[chara_id], 'NAME_EN': CHARA_NAMES_EN[chara_id],
        'NAME_SHORT_JA': CHARA_NAMES_SHORT_JA[chara_id],
        'NAME_SHORT_EN': CHARA_NAMES_SHORT_EN[chara_id],
        'DESC_JA': (
            f'STEP7で限定UR「お誕生日 {CHARA_NAMES_SHORT_JA[chara_id]}」確定！\n' +
            f'SR以上は「{CHARA_NAMES_SHORT_JA[chara_id]}」のみ出現！'
        ) if chara_id in range(1, 9) else (
            f'STEP7で「{CHARA_NAMES_SHORT_JA[chara_id]}」UR確定！\n' +
            f'SR以上は「{CHARA_NAMES_SHORT_JA[chara_id]}」のみ出現！'
        ),
        'DESC_EN': (
            f'Limited {CHARA_NAMES_SHORT_EN[chara_id]} birthday UR!\n' +
            f'SR and above are {CHARA_NAMES_SHORT_EN[chara_id]} only!'
        ) if chara_id in range(1, 9) else (
            f'SR and above are {CHARA_NAMES_SHORT_EN[chara_id]} only!'
        ),
        'BG': CHARA_BIRTHDAY_BGS[chara_id],
        'CHARAS': (chara_id,)
    })

# Exclusions:
# - the two bugged cards
# - team score event winning team reward cards
# - bonus cards given for specific holidays
#     (mainly because they're pair cards and not fairly distributed)
# - irl goods purchase bonus cards
# - story cards
# (N/R cards deliberately omitted because they aren't actually included)
# (still need to double check this)
EXCLUDE_CARDS = {
    150: None,
    # 151: None,
    # 162: ('【ラブサマ】', '[LoveSummer]'),  # Mei
    163: ('【ラブサマ】', '[LoveSummer]'),  # Mei
    # 186: ('【Halloween】', '[Halloween]'),  # Mei
    # 187: ('【Halloween】', '[Halloween]'),  # Hinata
    188: ('【Halloween】', '[Halloween]'),  # Mei
    189: ('【Halloween】', '[Halloween]'),  # Hinata
    210: ('【教官】', '[Professor]'),  # Hotaru
    222: ('【なかよし】', '[Close Friends]'),  # Yukina
    226: ('【クリスマス】', '[Christmas]'),  # Hinata
    231: ('【クリスマス】', '[Christmas]'),  # Ayame
    232: ('【クリスマス】', '[Christmas]'),  # Hotaru
    233: ('【クリスマス】', '[Christmas]'),  # Mei
    # 234: ('【ハピ♡メリ】', '[Happy♡Merry]'),  # Mei
    235: ('【ハピ♡メリ】', '[Happy♡Merry]'),  # Mei
    240: ('【ゲーマーズ】', '[Gamers]'),  # Hinata
    241: ('【アニメイト】', '[Animate]'),  # Suzune
    284: ('【修行の成果】', '[Fruits of our Labour]'),  # Mei
    241: ('【アニメイト】', '[Animate]'),  # Suzune
    # 285: ('【DREAMER】', '[DREAMER]'),  # Hinata
    286: ('【DREAMER】', '[DREAMER]'),  # Hinata
    287: ('【心にアクセサリー】', '[Accessory for the Heart]'),  # Anri
    345: ('【軌跡と奇跡】', '[My Past and That Miracle]'),  # Ayame
    # 357: ('【Rooting】', '[Rooting]'),  # Hotaru
    358: ('【Rooting】', '[Rooting]'),  # Hotaru
    382: ('【パーカー】', '[Parka]'),  # Hotaru
    # 422: ('【Twinkle】', '[Twinkle]'),  # Mei
    423: ('【Twinkle】', '[Twinkle]'),  # Mei
    436: ('【楽しんだもの勝ち】', '[Enjoying It Is the Real Win]'),  # Akari
    444: ('【自分の音】', '[My Own Sound]'),  # Suzune
    446: ('【かなでと一緒】', '[With Kanade]'),  # Hotaru
    447: ('【一緒に歌って】', '[Sing Along]'),  # Hotaru
    # 459: ('【サクラ涙】', '[Sakura Namida]'),  # Mei
    460: ('【サクラ涙】', '[Sakura Namida]'),  # Mei
    467: ('【みんなのアイドル】', '[Everyone\'s Idol]'),  # Yukina
    494: ('【そらまめ】', '[Soramame]'),  # Yukina
    # 506: ('【SUMMER BEAT】', '[SUMMER BEAT]'),  # Mei
    507: ('【SUMMER BEAT】', '[SUMMER BEAT]'),  # Mei
    # 548: ('【つよがり】', '[Tsuyogari]'),  # Ayame
    549: ('【つよがり】', '[Tsuyogari]'),  # Ayame
    # 581: ('【Precious Notes】', '[Precious Notes]'),  # Mei
    582: ('【Precious Notes】', '[Precious Notes]'),  # Mei
    609: ('【8/pLanet!!】', '[8/pLanet!!]')  # Hinata
}

# this is formatted for appending to gacha_type2_detail, just add ID field to all
STEPUP_DETAIL = [
    {
        # step 1: 11x pull for 150 jewels, no bonus
        'STEP': 1,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP1]$コアジュエル150個で11回ガチャ$11-pull for 150 Core Jewels',
        'BUTTON_IMAGE': 'btn_item2_150_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 150,
        'CARD_NUM': 11,
        'BONUS_ID': 0,
        'MEMO': 'なし'
    },
    {
        # step 2: 11x pull for 250 jewels, pickup card rate 2x
        'STEP': 2,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP2]$PICKUP 2倍$Pickup card rates x2',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 4,
        'MEMO': '1〜11枚目、PICKUP2倍'
    },
    {
        # step 3: 11x pull for 250 jewels, 2 SR+ guaranteed
        'STEP': 3,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP3]$SR以上2枚確定$2+ SR or UR guaranteed',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 5,
        'MEMO': '1〜11枚目、SR以上2枚確定'
    },
    {
        # step 4: 11x pull for 250 jewels, pickup card rate 4x
        'STEP': 4,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP4]$PICKUP 4倍$Pickup card rates x4',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 6,
        'MEMO': '1〜11枚目PICKUP4倍'
    },
    {
        # step 5: 11x pull for 250 jewels, 1 SR+ guaranteed, bonus 1x level limit up item
        'STEP': 5,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP5]$SR以上1枚確定$上限UPアイテム1つ$1+ SR or UR,$1 lvl limit up item',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 7,
        'MEMO': '1〜11枚目SR以上1枚確定、おまけでレベル上限UPアイテムをランダムで1つGET'
    },
    {
        # step 6: 11x pull for 250 jewels, 1 SR+ guaranteed, bonus 2x level limit up item
        'STEP': 6,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP6]$SR以上1枚確定$上限UPアイテム2つ$1+ SR or UR,$2 lvl limit up items',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 8,
        'MEMO': '1〜11枚目SR以上1枚確定、おまけでレベル上限UPアイテムをランダムで2つGET'
    },
    {
        # step 7: 11x pull for 250 jewels, 1 pickup card guaranteed
        'STEP': 7,
        'ENABLE_COUNT': 1,
        'DESC': '[STEP7]$11枚目に$PICKUP衣装確定$One pickup card guaranteed',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 9,
        'MEMO': '11枚目にPICKUPキャラ確定'
    }
]

STEPUP_RULES_TEXT_JA = '[STEP1]\n11回ガチャ\n使用コアジュエル:150個\n\n' + \
    '[STEP2]\n11回ガチャ\n使用コアジュエル：250個\n1〜11枚目でPICKUP2倍\n\n' + \
    '[STEP3]\n11回ガチャ\n使用コアジュエル：250個\n1〜11枚目でSR以上2枚確定\n\n' + \
    '[STEP4]\n11回ガチャ\n使用コアジュエル：250個\n1〜11枚目でPICKUP4倍\n\n' + \
    '[STEP5]\n11回ガチャ\n使用コアジュエル：250個\n1〜11枚目SR以上1枚確定、\nおまけでレベル上限UPアイテムをランダムで1つGET\n\n' + \
    '[STEP6]\n11回ガチャ\n使用コアジュエル：250個\n1〜11枚目SR以上1枚確定、\nおまけでレベル上限UPアイテムをランダムで2つGET\n\n' + \
    '[STEP7]\n11回ガチャ\n使用コアジュエル：250個\n11枚目にPICKUP衣装確定'

STEPUP_RULES_TEXT_EN = '[STEP1]\n・11-times gacha\n・Cost: 150 core jewels\n\n' + \
    '[STEP2]\n・11-times gacha\n・Cost: 250 core jewels\n・Pickup card appearance rates x2\n\n' + \
    '[STEP3]\n・11-times gacha\n・Cost: 250 core jewels\n・At least 2 SR or better cards guaranteed\n\n' + \
    '[STEP4]\n・11-times gacha\n・Cost: 250 core jewels\n・Pickup card appearance rates x4\n\n' + \
    '[STEP5]\n・11-times gacha\n・Cost: 250 core jewels\n' + \
        '・At least 1 SR or better card guaranteed\n・Get one bonus level limit increase item\n\n' + \
    '[STEP6]\n・11-times gacha\n・Cost: 250 core jewels\n' + \
        '・At least 1 SR or better card guaranteed\n・Get two bonus level limit increase items\n\n' + \
    '[STEP7]\n・11-times gacha\n・Cost: 250 core jewels\n・One pickup card guaranteed'

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

WEEKDAYS_JA = {
    0: '月',
    1: '火',
    2: '水',
    3: '木',
    4: '金',
    5: '土',
    6: '日'
}
WEEKDAYS_EN = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thu',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun'
}

HTML_TABLE_STRINGS_JA = {
    'date': 'Date',
    'date_format': '%m月%d日',
    'image': 'Image',
    'contents': 'Pickup Cards'
}
HTML_TABLE_STRINGS_EN = {
    'date': 'Date',
    'date_format': '%m/%d',
    'image': 'Image',
    'contents': 'Pickup Cards'
}

HTML_TABLE_STYLE = '''<style>
    table.gacha-schedule-birthday {
        border: 2px solid black;
        border-spacing: 0;
        margin: 0.5em 0;
    }
    table.gacha-schedule-birthday th, table.gacha-schedule-birthday td {
        border: 1px solid black;
        padding: 0.05em 0.25em;
    }
</style>'''

HTML_BANNER_IMAGE_PATH = 'static/gacha/img_banner2_{id}.png'


def _gen_birthday_gacha_banner_image_ja(
        banner_dict: dict,
        image_cards: list[CardDetail],
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    bg_name = banner_dict['BG']
    description_text = banner_dict['DESC_JA']

    is_single_chara_banner = len(set([c.chara for c in image_cards])) == 1

    # randomly select up to four cards if multiple characters (max of one per character),
    # or three cards if single character
    image_cards = image_cards.copy()
    shuffled_image_cards = []
    rd = random.Random(output_gacha_id)
    for _ in range(3 if is_single_chara_banner else 4):
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

    return gen_stepup_gacha_banner_image(
        bg_name,
        [f'image/chara/stand/stand_chara{id}_2.png' for id in shuffled_image_cards],
        'Birthdayステップアップガチャ',
        description_text,
        resource_path,
        ver
    )


def _check_exclusion_names(master_chara: List[dict]):
    """Verify that the Japanese card names in EXCLUDE_CARDS match master_chara.

    Will assert if any are incorrect. Just to make sure there's no typo'd IDs.
    """
    for k, v in EXCLUDE_CARDS.items():
        # ignore if no name set in EXCLUDE_CARDS
        if not v or not v[0]:
            continue

        row = [x for x in master_chara if x['ID'] == k][0]
        assert v[0] in row['NAME']


def _chara_birthday_cards(master_chara: List[dict], chara_id: int) -> List[CardDetail]:
    """Create a list of all birthday cards for given character ID.

    Cards in EXCLUDE_CARDS are excluded from the list.
    """
    rows = [x for x in master_chara if x['NO'] == chara_id and '【お誕生日】' in x['NAME']]
    rows = [x for x in rows if x['ID'] not in EXCLUDE_CARDS]
    return [CardDetail(x['NO'], x['ID'], x['RARE'], x['NAME'], x['SERIES'], x['BG'])
            for x in rows]

def _chara_sr_ur_cards(master_chara: List[dict], chara_id: int) -> List[CardDetail]:
    """Create a list of all SR and UR cards for given character ID.

    Cards in EXCLUDE_CARDS are excluded from the list.
    """
    rows = [x for x in master_chara if x['NO'] == chara_id and x['RARE'] >= 3]
    rows = [x for x in rows if x['ID'] not in EXCLUDE_CARDS]
    return [CardDetail(x['NO'], x['ID'], x['RARE'], x['NAME'], x['SERIES'], x['BG'])
            for x in rows]

def _chara_exclude_card_names(master_chara: List[dict], chara_id: int) -> List[tuple]:
    """Create a list of all excluded card names for given character ID.

    Returned tuples are (series_name_ja, series_name_en).
    (With brackets included in names.)
    """
    rows = [x for x in master_chara if x['NO'] == chara_id]
    return [EXCLUDE_CARDS[x['ID']] for x in rows if x['ID'] in EXCLUDE_CARDS]

def _all_permanent_r_cards(permanent_gacha_data: List[dict]) -> List[CardDetail]:
    """Create a list of all cards of R rarity in permanent gacha.

    Cards in EXCLUDE_CARDS are excluded from the list.
    """
    rows = []
    for series in permanent_gacha_data:
        cards = [x for x in series['CARDS'] if x.rarity == 2]
        rows.extend(cards)
    rows = [x for x in rows if x.id not in EXCLUDE_CARDS]
    return rows


def _gen_banner_limited_data(master_chara: List[dict], banner: dict) -> dict:
    data = {
        'DURATION_DAYS': 5,
        'START_DATE': banner['DATE'],  # change format because should land on exact date
        'BANNER_TEXT_JA': f'「{banner["NAME_JA"]}」誕生日ガチャ',
        'BANNER_TEXT_EN': f'{banner["NAME_EN"]} birthday gacha',
        'BANNER_BG': banner['BG']
    }

    charas = banner['CHARAS']
    if len(charas) == 1 and charas[0] in range(1, 9):
        data['UR_DESC_TEXT_JA'] = f'【お誕生日】{banner["NAME_SHORT_JA"]}'
        data['UR_DESC_TEXT_EN'] = f'[Birthday] {banner["NAME_SHORT_EN"]}'
        data['CARDS'] = _chara_birthday_cards(master_chara, charas[0])
    else:
        data['CARDS'] = []  # no limited/pickup cards

    return data

def _gen_banner_other_data(
        master_chara: List[dict],
        permanent_gacha_data: List[dict],
        banner: dict
    ) -> dict:
    data = {}
    cards = []
    ur_desc_text_ja = f'「{banner["NAME_JA"]}」のUR衣装全部'
    ur_desc_text_en = f'All {banner["NAME_SHORT_EN"]} UR cards'
    sr_desc_text_ja = f'「{banner["NAME_JA"]}」のSR衣装全部（イベント衣装込）'
    sr_desc_text_en = f'All {banner["NAME_SHORT_EN"]} SR cards (including event cards)'
    r_desc_text_ja = 'プレミアムガチャで登場衣装と同じ'
    r_desc_text_en = 'Same as premium gacha'

    charas = banner['CHARAS']
    for chara_id in charas:
        bd_cards = _chara_birthday_cards(master_chara, chara_id)
        sr_ur_cards = _chara_sr_ur_cards(master_chara, chara_id)
        sr_ur_cards = [c for c in sr_ur_cards if not c in bd_cards]
        cards.extend(sr_ur_cards)

    cards.extend(_all_permanent_r_cards(permanent_gacha_data))

    return {
        'CARDS': cards,
        'UR_DESC_TEXT_JA': ur_desc_text_ja,
        'UR_DESC_TEXT_EN': ur_desc_text_en,
        'SR_DESC_TEXT_JA': sr_desc_text_ja,
        'SR_DESC_TEXT_EN': sr_desc_text_en,
        'R_DESC_TEXT_JA': r_desc_text_ja,
        'R_DESC_TEXT_EN': r_desc_text_en
    }


def _gacha_short_contents_text(
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        appearance_rates: dict,
        lang_code: str
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
                text += lim_desc_text + '\n'

        for series in permanent_gacha_data:
            perm_desc_text = series.get(desc_text_key, '').strip()
            if perm_desc_text:
                text += perm_desc_text + '\n'

        if not text:
            return ''

        text = f'{rarity}:\n' + text + '\n'
        return text

    contents_text = contents_string_for_rarity('UR')
    contents_text += contents_string_for_rarity('SR')
    contents_text += contents_string_for_rarity('R')
    contents_text += contents_string_for_rarity('N')
    return contents_text.strip()

def _gacha_list_entry(
        banner_dict: dict,
        other_gacha_data: dict,  # note: = non-limited for this banner
        limited_gacha_data_dict: dict,
        first_gacha_id: int,
        master_chara: List[dict],
        resource_path: str,
        ver: int
    ) -> dict:
    # use all of chara's UR cards as pickup if no pickup set (no birthday cards)
    appearance_rates = GACHA_ODDS.copy()
    limited_cards = limited_gacha_data_dict['CARDS']
    if len(limited_cards) == 0:
        limited_gacha_data_dict = limited_gacha_data_dict.copy()
        other_gacha_data = other_gacha_data.copy()
        other_cards = other_gacha_data['CARDS']

        limited_cards = [c for c in other_cards if c.rarity == 4]
        other_cards = [c for c in other_cards if c.rarity != 4]

        limited_gacha_data_dict['CARDS'] = limited_cards
        other_gacha_data['CARDS'] = other_cards
        # need to adjust UR appearance rates to make LIMITED_UR == TOTAL_UR now
        appearance_rates['LIMITED_UR'] = appearance_rates['TOTAL_UR']

        # update description text
        limited_gacha_data_dict['UR_DESC_TEXT_JA'] = f'「{banner_dict["NAME_JA"]}」のUR衣装全部'
        limited_gacha_data_dict['UR_DESC_TEXT_EN'] = f'All {banner_dict["NAME_SHORT_EN"]} UR cards'
        other_gacha_data['UR_DESC_TEXT_JA'] = 'なし'
        other_gacha_data['UR_DESC_TEXT_EN'] = 'None'

    banner_image = _gen_birthday_gacha_banner_image_ja(banner_dict, limited_cards,
                                                       first_gacha_id, resource_path, ver)
    banner_image = image_quantize(banner_image)
    # banner_image.save(f'gacha_banners/img_banner2_{first_gacha_id}.png')

    excluded_series = []
    charas = banner_dict['CHARAS']
    for chara_id in charas:
        excluded_series.extend(_chara_exclude_card_names(master_chara, chara_id))

    excluded_series_ja = list((x[0] for x in excluded_series if x))
    excluded_series_en = list((x[1] for x in excluded_series if x))
    desc_text = gen_gacha_stepup_description_text_combined([other_gacha_data],
                                                           limited_gacha_data_dict,
                                                           appearance_rates,
                                                           excluded_series_ja,
                                                           excluded_series_en,
                                                           STEPUP_RULES_TEXT_JA,
                                                           STEPUP_RULES_TEXT_EN)
    # with open(f'gacha_banners/banner{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     f.write(desc_text)

    limited_contents_text_ja = _gacha_short_contents_text([], limited_gacha_data_dict,
                                                          appearance_rates, 'ja')
    limited_contents_text_en = _gacha_short_contents_text([], limited_gacha_data_dict,
                                                          appearance_rates, 'en')

    per_table = gen_gacha_stepup_per_table([other_gacha_data], limited_gacha_data_dict,
                                           appearance_rates)
    # with open(f'gacha_banners/table{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     json.dump(per_table, f)

    print(f'Gacha entry generated, id={first_gacha_id}')

    return {
        'first_gacha_id': first_gacha_id,
        'banner_image': banner_image,
        'desc_text': desc_text,
        'per_table': per_table,
        'limited_data': limited_gacha_data_dict,
        'other_data': other_gacha_data,
        'limited_contents_text_ja': limited_contents_text_ja,
        'limited_contents_text_en': limited_contents_text_en
    }

def _master_gacha_row(entry: dict, gacha_id: int, year: int) -> dict:
    limited_data = entry.get('limited_data')
    start_date = limited_data['START_DATE'].replace(year=year)
    # note: end_date is day *after* end, not day of end
    end_date = start_date + timedelta(days=limited_data['DURATION_DAYS'])

    desc_text = entry['desc_text'].replace('\n', '$')
    if start_date:  # useless to check, but looks nice visually
        desc_text = desc_text.replace('<START_MONTH>', str(start_date.month))
        desc_text = desc_text.replace('<START_DAY>', str(start_date.day))
        weekday = start_date.weekday()
        desc_text = desc_text.replace('<START_WEEKDAY_JA>', WEEKDAYS_JA.get(weekday))
        desc_text = desc_text.replace('<START_WEEKDAY_EN>', WEEKDAYS_EN.get(weekday))
    if end_date:
        # description text says until 11:59 of day before end date in date
        desc_end_date = end_date - timedelta(days=1)
        desc_text = desc_text.replace('<END_MONTH>', str(desc_end_date.month))
        desc_text = desc_text.replace('<END_DAY>', str(desc_end_date.day))
        weekday = desc_end_date.weekday()
        desc_text = desc_text.replace('<END_WEEKDAY_JA>', WEEKDAYS_JA.get(weekday))
        desc_text = desc_text.replace('<END_WEEKDAY_EN>', WEEKDAYS_EN.get(weekday))

    return {
        'ID': gacha_id,
        'GACHA_TYPE': 2,  # step-up
        'NAME': 'ステップアップガチャ',
        'ORDER': 3,  # seems to be based on type
        'BANNER': f'img_banner2_{entry["first_gacha_id"]}',
        'DETAIL': desc_text,
        'USE_ITEM': 0,
        'GACHA_1': 0,
        'GACHA_10': 0,
        'GACHA_11': 0,
        'SR_SET': 0,
        'SHEET': f'gacha_type2_{entry["first_gacha_id"]}',
        'SHEET_DAILY': 0,
        'FROM_INSTALL': 0,
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

def _gen_schedule_html_table(
        entries: List[dict],
        strings: Dict[str, str],
        contents_key: str,
        indent: str='    '
    ) -> str:
    output = HTML_TABLE_STYLE + '\n'
    output += '<table class="gacha-schedule-birthday">\n'
    output += indent + '<tr>\n'
    output += indent*2 + f'<th>{strings.get("date")}</th>\n'
    output += indent*2 + f'<th>{strings.get("image")}</th>\n'
    output += indent*2 + f'<th>{strings.get("contents")}</th>\n'
    output += indent + '</tr>\n'

    for entry in entries:
        limited_data = entry.get('limited_data')
        if not limited_data:
            continue

        output += indent + '<tr>\n'

        date_str = limited_data['START_DATE'].strftime(strings.get('date_format'))
        date_cell = f'<td>{date_str}</td>'
        date_cell = indent*2 + date_cell + '\n'

        image_path = HTML_BANNER_IMAGE_PATH.format(id=entry["first_gacha_id"])
        image_tag = f'<img src="{image_path}" width=240 height=80 />'
        image_tag = indent*3 + image_tag + '\n'
        image_cell = indent*2 + '<td>\n' + image_tag + indent*2 + '</td>\n'

        contents_text = entry.get(contents_key)
        contents_text = contents_text.replace('\n', '<br>')
        contents_text = '<p>' + contents_text.replace('<br><br>', '<p>')
        contents_cell = f'<td>{contents_text}</td>'
        contents_cell = indent*2 + contents_cell + '\n'

        output += date_cell
        output += image_cell
        output += contents_cell
        output += indent + '</tr>\n'

    output += '</table>'
    return output

def _gen_markdown_page_en(stepup_gacha_unique_entires: List[dict]) -> str:
    output = '# Birthday Gacha\n\n'
    output += 'Step-up gacha is enabled on members\' birthdays, lasting for five days.\n'
    output += 'All SR and UR cards pulled will be the birthday girl(s), '
    output += 'and you can pull most event SRs!\n\n'
    output += 'The special pickup cards will have boosted odds,'
    output += 'and one of them is guaranteed on step 7.\n\n'

    output += _gen_schedule_html_table(stepup_gacha_unique_entires, HTML_TABLE_STRINGS_EN,
                                       'limited_contents_text_en')

    return output


def gen_gacha_birthday_stepup(resource_path, ver, start_year, end_year):
    master_chara = read_json_decrypted(resource_path, ver, 'json/master_chara.json')
    master_chara = json.loads(master_chara)
    master_series = read_json_decrypted(resource_path, ver, 'json/master_series.json')
    master_series = json.loads(master_series)
    master_gacha_main = read_json_decrypted(resource_path, ver, 'json/master_gacha_main.json')
    master_gacha_main = json.loads(master_gacha_main)
    master_gacha_type2_1 = read_json_decrypted(resource_path, ver, 'json/master_gacha_type2_1.json')
    master_gacha_type2_1 = json.loads(master_gacha_type2_1)
    master_gacha_type2_detail = read_json_decrypted(resource_path, ver, 'json/master_gacha_type2_detail.json')
    master_gacha_type2_detail = json.loads(master_gacha_type2_detail)

    permanent_gacha_data = load_and_parse_gacha_data_csv(PERMANENT_CSV_PATH)
    set_card_names_from_master_chara(permanent_gacha_data, master_chara)
    set_card_series_from_master_chara(permanent_gacha_data, master_chara)
    set_card_gacha_bg_from_master_chara(permanent_gacha_data, master_chara)

    # don't bother verifying the permanent_gacha_data
    # -- assume it's fine from doing the regular gacha rotation

    gacha_id = max([row['ID'] for row in master_gacha_main[1:]]) + 1
    # go up to next multiple of 1000, so it's neat
    gacha_id = math.ceil(gacha_id / 1000) * 1000
    first_gacha_id = gacha_id  # first occurence of each entry

    stepup_gacha_unique_entires = []
    for banner in BIRTHDAY_BANNERS:
        limited_data = _gen_banner_limited_data(master_chara, banner)
        other_data = _gen_banner_other_data(master_chara, permanent_gacha_data, banner)
        entry = _gacha_list_entry(banner, other_data, limited_data, first_gacha_id,
                                  master_chara, resource_path, ver)
        stepup_gacha_unique_entires.append(entry)
        first_gacha_id += 1

    # print(stepup_gacha_unique_entires)

    master_gacha_rows = []
    for year in range(start_year, end_year + 1):
        for entry in stepup_gacha_unique_entires:
            master_gacha_rows.append(_master_gacha_row(entry, gacha_id, year))
            gacha_id += 1

    # print(master_gacha_rows)


    # output markdown page and web images
    md = _gen_markdown_page_en(stepup_gacha_unique_entires)
    with open(f'gacha_md/birthday.md', 'w', encoding='utf-8') as f:
        f.write(md)

    for entry in stepup_gacha_unique_entires:
        first_id = entry['first_gacha_id']
        # resize because no need for such large images on web
        banner_image = entry['banner_image'].convert('RGBA').resize((480, 160))
        banner_image = image_quantize(banner_image)
        banner_image.save(f'gacha_md/static/gacha/img_banner2_{first_id}.png')


    # add gacha detail sheets
    replacements = {}
    for entry in stepup_gacha_unique_entires:
        header_row = master_gacha_type2_1[0]
        full_table = [header_row] + entry['per_table']
        first_id = entry["first_gacha_id"]
        replacements[f'json/master_gacha_type2_{first_id}.json'] = json.dumps(full_table)
    replacements = encrypt_replacements_json(replacements)
    zip_path = path_join(resource_path, str(ver), '1_json01.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

    # add step details
    for row in master_gacha_rows:
        gacha_id = row['ID']
        detail_rows = [{'ID': gacha_id} | x for x in STEPUP_DETAIL]
        master_gacha_type2_detail.extend(detail_rows)
    replacements = encrypt_replacements_json({
        'json/master_gacha_type2_detail.json': json.dumps(master_gacha_type2_detail)
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # merge and replace master_gacha_main
    master_gacha_main.extend(master_gacha_rows)
    replacements = encrypt_replacements_json({
        'json/master_gacha_main.json': json.dumps(master_gacha_main)
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # add images
    replacements = {}
    for entry in stepup_gacha_unique_entires:
        io = BytesIO()
        entry['banner_image'].save(io, format='PNG')
        first_id = entry["first_gacha_id"]
        replacements[f'image/event/gacha/2/img_banner2_{first_id}.png'] = io.getvalue()
    zip_path = path_join(resource_path, str(ver), '1_pkg.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 5:
        print('Usage: python gen_gacha_birthday_stepup.py <resource_path> <ver> <start_year> <end_year>')
        print('Example: python gen_gacha_birthday_stepup.py res 733 2026 2031')
        exit()

    gen_gacha_birthday_stepup(argv[1], int(argv[2]), int(argv[3]), int(argv[4]))
