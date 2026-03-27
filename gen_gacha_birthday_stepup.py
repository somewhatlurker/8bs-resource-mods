# Generate birthday gacha banners in step-up gacha.
# The banner contains only the birthday girl's cards for SR and UR rarities

# WORK IN PROGRESS, COMPLETELY NON-FUNCTIONAL AND UNTESTED

from typing import List

from gacha_data.load_gacha_data import CardDetail


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
    15: 'Bellum',
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
    15: 'Bellum',
}

# Exclusions:
# - the two bugged cards
# - team score event winning team reward cards
# - bonus cards given for specific holidays
#     (mainly because they're pair cards and not fairly distributed)
# - irl goods purchase bonus cards
# - story cards
# (Limited to SR and UR cards only)
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

def _all_non_event_n_r_cards(master_chara: List[dict]) -> List[CardDetail]:
    """Create a list of all non-event cards of N or R rarity.

    Cards in EXCLUDE_CARDS are excluded from the list.
    """
    rows = [x for x in master_chara if x['SERIES'] != 17 and x['RARE'] < 3]
    rows = [x for x in rows if x['ID'] not in EXCLUDE_CARDS]
    return [CardDetail(x['NO'], x['ID'], x['RARE'], x['NAME'], x['SERIES'], x['BG'])
            for x in rows]
