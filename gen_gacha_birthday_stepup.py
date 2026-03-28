# Generate birthday gacha banners in step-up gacha.
# The banner contains only the birthday girl's cards for SR and UR rarities
# (including event cards).
# R rarity includes the same cards as permanent gacha.

# WORK IN PROGRESS, COMPLETELY NON-FUNCTIONAL AND UNTESTED

from datetime import date, timedelta
from decimal import Decimal
import random
from typing import List

from PIL import Image

from gacha_data.load_gacha_data import CardDetail
from gen_gacha_banner_image import gen_gacha_banner_image


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
# Add all of 8/pLanet!!, Kanade, and 2_wEi (sorted by birthday)
for chara_id in (7, 4, 5, 3, 2, 8, 6, 10, 11, 12, 1):
    BIRTHDAY_BANNERS.append({
        'DATE': CHARA_BIRTHDAYS[chara_id],
        'NAME_JA': CHARA_NAMES_JA[chara_id], 'NAME_EN': CHARA_NAMES_EN[chara_id],
        'NAME_SHORT_JA': CHARA_NAMES_SHORT_JA[chara_id],
        'NAME_SHORT_EN': CHARA_NAMES_SHORT_EN[chara_id],
        'DESC_JA': (
            f'限定UR「お誕生日 {CHARA_NAMES_SHORT_JA[chara_id]}」登場！\n' +
            f'SR以上は「{CHARA_NAMES_SHORT_JA[chara_id]}」のみ出現！'
        ) if chara_id in range(1, 8) else (
            f'SR以上は「{CHARA_NAMES_SHORT_JA[chara_id]}」のみ出現！'
        ),
        'DESC_EN': (
            f'Limited {CHARA_NAMES_SHORT_EN[chara_id]} birthday UR!\n' +
            f'SR and above are {CHARA_NAMES_SHORT_EN[chara_id]} only!'
        ) if chara_id in range(1, 8) else (
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
    210: ('【教官】', '[Professor] Hotaru'),  # Hotaru
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
        'DESC': '[STEP1]$コアジュエル150個で11回ガチャ$Pull 11 times for 150 Core Jewels',
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
        'DESC': '[STEP2]$1〜11枚目でPICKUP 2倍$Pickup card appearance rates x2',
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
        'DESC': '[STEP3]$1〜11枚目でSR以上2枚確定$At least 2 SR or better cards guaranteed',
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
        'DESC': '[STEP4]$1〜11枚目でPICKUP 4倍$Pickup card appearance rates x4',
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
        'DESC': '[STEP5]$1〜11枚目でSR以上1枚確定、上限UPアイテム1つ$At least 1 SR or better card,$Get a level limit increase item',
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
        'DESC': '[STEP5]$1〜11枚目でSR以上1枚確定、上限UPアイテム2つ$At least 1 SR or better card,$Get two level limit increase items',
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
        'DESC': '[STEP7]$11枚目にPICKUP衣装確定$Pickup card guaranteed',
        'BUTTON_IMAGE': 'btn_item2_250_11',
        'USE_ITEM_ID': 2,
        'USE_ITEM_NUM': 250,
        'CARD_NUM': 11,
        'BONUS_ID': 9,
        'MEMO': '11枚目にPICKUPキャラ確定'
    }
]

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


def _gen_birthday_gacha_banner_image_ja(
        banner_dict: dict,
        image_cards: list[CardDetail],
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    # 'DATE': date(1900, 1, 11),
    # 'NAME_JA': 'B.A.Cメンバー', 'NAME_EN': 'B.A.C Members\'',
    # 'NAME_SHORT_JA': 'B.A.C', 'NAME_SHORT_EN': 'B.A.C',
    # 'DESC_JA': 'SR以上はB.A.Cメンバーのみ出現！',
    # 'DESC_EN': 'SR and above are B.A.C members only!',
    # 'BG': 'bg222',
    # 'CHARAS': (13, 14, 15)
    bg_name = banner_dict['BG']
    description_text = banner_dict['DESC_JA']

    is_single_chara_banner = len(set([c.chara for c in image_cards])) == 1

    # randomly select up to four cards if multiple characters (max of one per character),
    # or two cards if single character
    shuffled_image_cards = []
    rd = random.Random(output_gacha_id)
    for _ in range(2 if is_single_chara_banner else 4):
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
        'Birthday',
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
