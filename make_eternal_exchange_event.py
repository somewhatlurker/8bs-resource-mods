# makes an eternal (until 2038) exchange event (BIT fest), containing all event SR cards

import json
from os.path import join as path_join

from util import encrypt_replacements_json, read_file, read_json_decrypted, \
                 replace_files_in_ver, replace_files_in_zip


def make_eternal_exchange_event(resource_path, ver):
    # take event card list from card series 17 (event/promo),
    # but remove these non-event cards from it
    EVENT_CARD_EXCLUSIONS = (
        # lovely summer placeholders
        150, 151,

        # birthday cards
        327, 335, 350, 367, 388, 435, 443, 454, 481, 488, 503, 514, 539, 556, 559, 568,
        591, 596, 607, 618, 630, 642, 643, 650, 692, 697, 700, 706, 710, 711, 712, 713,
        716, 717, 718, 730, 749, 759, 760, 764, 779, 780, 788, 792, 795, 808, 809, 813,

        # in-game presents/rewards (other than events)
        210, 222,

        # cards given away with goods
        240, 241, 382, 494,

        # story cards
        284, 287, 345, 436, 444, 446, 447, 467, 609,
    )


    # load and prepare data
    events_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_events.json'))
    event_exchange_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_event_exchange.json'))
    reward_main_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_exchange_event_reward_main.json'))
    reward_personal_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_exchange_event_reward_personal.json'))
    rule_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_rule.json'))
    event_daily_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_event_daily.json'))
    top_banner_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_top_banner.json'))
    chara_json = json.loads(read_json_decrypted(
        resource_path, ver, 'json/master_chara.json'))

    EVENT_ID = max(x['ID'] for x in events_json[1:]) + 1  # overall ID in master_events
    BIT_EVENT_ID = max(x['EVENT_ID'] for x in event_exchange_json[1:]) + 1  # ID within BIT event type
    REWARD_PERSONAL_ID = max(x['ID'] for x in reward_personal_json[1:]) + 1  # claimable reward entries ID
    REWARD_MAIN_ID = max(x['ID'] for x in reward_main_json[1:]) + 1  # showcased card entries ID
    RULE_ID = max(x['ID'] for x in rule_json[1:]) + 1  # event rule 'story' ID
    EVENT_DAILY_ID = max(x['ID'] for x in event_daily_json[1:]) + 1  # item drop rule ID
    TOP_BANNER_ID = max(x['ID'] for x in top_banner_json[1:]) + 1   # home screen banner ID

    # master_chara entries for matching cards
    EVENT_CARDS = [
        x for x in chara_json
        if x['SERIES'] == 17 and x['ID'] not in EVENT_CARD_EXCLUSIONS
    ]


    ################################################################################
    # HUGE block of data -- scroll down ~230 lines to reach more code              #
    ################################################################################
    events_entry = {
        'ID': EVENT_ID, 'TITLE': 'EternalBIT',
        'TYPE': 2,  # 1: score/token, 2: exchange/bit, 3: team score,
                    # 4: chara levelup, 5: pvp, 6: song request
        'EVENT_ID': BIT_EVENT_ID,
        'START_YEAR': 2025, 'START_MONTH': 1, 'START_DAY': 1,  # start of event
        'START_HOUR' : 0, 'START_MINUTE': 0,
        'SPURT_YEAR': 2038,  'SPURT_MONTH': 1, 'SPURT_DAY': 1,  # start of boost mode
        'SPURT_HOUR': 0, 'SPURT_MINUTE': 0,
        'END_YEAR': 2038, 'END_MONTH': 1, 'END_DAY': 1,  # end of event (playable period)
        'END_HOUR': 0, 'END_MINUTE': 0,
        'FINISH_YEAR': 0, 'FINISH_MONTH': 0, 'FINISH_DAY': 0,  # not used for exchange?
        'FINISH_HOUR': 0, 'FINISH_MINUTE': 0,
        'DELIVERY_YEAR': 0, 'DELIVERY_MONTH': 0, 'DELIVERY_DAY': 0,  # not used for exchange?
        'DELIVERY_HOUR': 0, 'DELIVERY_MINUTE': 0,
        'COMPLETE_YEAR': 2038, 'COMPLETE_MONTH': 1, 'COMPLETE_DAY': 1,  # when the exchange closes (can no longer spend points)
        'COMPLETE_HOUR': 0, 'COMPLETE_MINUTE': 0
    }

    event_exchange_entry = {
        'EVENT_ID': BIT_EVENT_ID, 'TITLE': 'EternalBIT',
        'REWARD_PERSONAL_ID': REWARD_PERSONAL_ID, 'REWARD_MAIN_ID': REWARD_MAIN_ID,
        'BGM': 'music1',  # song that plays in exchange
        'BG': 'bg_live_1.png',  # background image in exchange
        'RULE_ID': RULE_ID
    }

    reward_main_entries = [
        {
            'ID': REWARD_MAIN_ID, 'SUB_ID': i+1, 'IMG': card['ID'],
            'TITLE': 'イベントPt 2,000で交換'
        }
        for i, card in enumerate(EVENT_CARDS)
    ]

    reward_personal_card_entries = [
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': i+1, 'POINT': 2000, 'TITLE': card['NAME'],
            'MESSAGE': 'BITフェスタ交換報酬', 'ITEM_TYPE': 2, 'ITEM_ID': card['ID'],
            'ITEM_NUM': 1, 'IMG': 0, 'NUM_EXCHANGE_MAX': 3, 'PRESENT_TITLE': card['NAME']
        }
        for i, card in enumerate(EVENT_CARDS)
    ]

    # items from ID 77, limits multiplied by ~8
    reward_personal_item_entries = [
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 1 + len(reward_personal_card_entries),
            'POINT': 8888, 'TITLE': 'URガチャチケット', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 4, 'ITEM_ID': 2, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': 'URガチャチケット'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 2 + len(reward_personal_card_entries),
            'POINT': 4500, 'TITLE': 'SRチケットPlus', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 4, 'ITEM_ID': 3, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': 'SRチケットPlus'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 3 + len(reward_personal_card_entries),
            'POINT': 1500, 'TITLE': 'SRガチャチケット', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 4, 'ITEM_ID': 1, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': 'SRガチャチケット'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 4 + len(reward_personal_card_entries),
            'POINT': 1250, 'TITLE': 'URチケットMini', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 16, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 16, 'PRESENT_TITLE': 'URチケットMini'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 5 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.ひなた', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 17, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.ひなた'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 6 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.鈴音', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 18, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.鈴音'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 7 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.月', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 19, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.月'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 8 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.彩芽', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 20, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.彩芽'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 9 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.杏梨', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 21, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.杏梨'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 10 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.ゆきな', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 22, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.ゆきな'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 11 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.ほたる', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 23, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.ほたる'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 12 + len(reward_personal_card_entries),
            'POINT': 2000, 'TITLE': '上限突破 Ver.メイ', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 24, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '上限突破 Ver.メイ'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 13 + len(reward_personal_card_entries),
            'POINT': 300, 'TITLE': 'コアジュエル × 5', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 0, 'ITEM_ID': 2, 'ITEM_NUM': 5, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 24, 'PRESENT_TITLE': 'コアジュエル'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 14 + len(reward_personal_card_entries),
            'POINT': 180, 'TITLE': 'ストーリーPt × 50', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 0, 'ITEM_ID': 7, 'ITEM_NUM': 50, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 24, 'PRESENT_TITLE': 'ストーリーPt'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 15 + len(reward_personal_card_entries),
            'POINT': 300, 'TITLE': '部室増築 × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 15, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 24, 'PRESENT_TITLE': '部室増築'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 16 + len(reward_personal_card_entries),
            'POINT': 150, 'TITLE': 'スキルUPマイク+ × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 14, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 88, 'PRESENT_TITLE': 'スキルUPマイク+'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 17 + len(reward_personal_card_entries),
            'POINT': 120, 'TITLE': 'スキルUPマイク × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 13, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 175, 'PRESENT_TITLE': 'スキルUPマイク'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 18 + len(reward_personal_card_entries),
            'POINT': 150, 'TITLE': 'エナブルHigh × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 7, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 48, 'PRESENT_TITLE': 'エナブルHigh'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 19 + len(reward_personal_card_entries),
            'POINT': 90, 'TITLE': 'エナブルLow × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 6, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 48, 'PRESENT_TITLE': 'エナブルLow'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 20 + len(reward_personal_card_entries),
            'POINT': 300, 'TITLE': '強化プログラムS × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 12, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 16, 'PRESENT_TITLE': '強化プログラムS'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 21 + len(reward_personal_card_entries),
            'POINT': 200, 'TITLE': '強化プログラムA × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 11, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 16, 'PRESENT_TITLE': '強化プログラムA'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 22 + len(reward_personal_card_entries),
            'POINT': 120, 'TITLE': '音の結晶 × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 5, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '音の結晶'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 23 + len(reward_personal_card_entries),
            'POINT': 120, 'TITLE': '音の花 × 1', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 4, 'ITEM_NUM': 1, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '音の花'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 24 + len(reward_personal_card_entries),
            'POINT': 60, 'TITLE': '音の蕾 × 3', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 3, 'ITEM_NUM': 3, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '音の蕾'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 25 + len(reward_personal_card_entries),
            'POINT': 60, 'TITLE': '音の葉 × 3', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 2, 'ITEM_NUM': 3, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '音の葉'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 26 + len(reward_personal_card_entries),
            'POINT': 60, 'TITLE': '音の種 × 3', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 1, 'ITEM_ID': 1, 'ITEM_NUM': 3, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 8, 'PRESENT_TITLE': '音の種'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 27 + len(reward_personal_card_entries),
            'POINT': 1000, 'TITLE': 'コイン × 10000', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 0, 'ITEM_ID': 1, 'ITEM_NUM': 10000, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 0, 'PRESENT_TITLE': 'コイン'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 28 + len(reward_personal_card_entries),
            'POINT': 100, 'TITLE': 'コイン × 1000', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 0, 'ITEM_ID': 1, 'ITEM_NUM': 1000, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 0, 'PRESENT_TITLE': 'コイン'
        },
        {
            'ID': REWARD_PERSONAL_ID, 'SUB_ID': 29 + len(reward_personal_card_entries),
            'POINT': 1, 'TITLE': 'コイン × 10', 'MESSAGE': 'BITフェスタ交換報酬',
            'ITEM_TYPE': 0, 'ITEM_ID': 1, 'ITEM_NUM': 10, 'IMG': 0,
            'NUM_EXCHANGE_MAX': 0, 'PRESENT_TITLE': 'コイン'
        }
    ]

    reward_personal_entries = reward_personal_card_entries + reward_personal_item_entries

    rule_entries = [
        {
            'ID': RULE_ID, 'SUB_ID': 1,
            'MESSAGE': '「EternalBIT」とは永遠まで続けるBITフェスタです！$$Ptでイベント限定メンバーを全部手に入れます！',
            'BTN_FILE': 'btn_next.png', 'IMAGE_FILE': 'img_rule2_1.png',
            'BG_FILE': 'bg_live_1.png'
        },
        {
            'ID': RULE_ID, 'SUB_ID': 2,
            'MESSAGE': 'スケジュール無し、イベントは止まらないぞ！',
            'BTN_FILE': 'btn_next.png', 'IMAGE_FILE': '../../bg/bg_live_1.png',
            'BG_FILE': 'bg_live_1.png'
        },
        {
            'ID': RULE_ID, 'SUB_ID': 3,
            'MESSAGE': '「ブーストモード!!」もない！ゆっくり遊んでくださいね！',
            'BTN_FILE': 'btn_next.png', 'IMAGE_FILE': '../../bg/bg_live_1.png',
            'BG_FILE': 'bg_live_1.png'
        },
        {
            'ID': RULE_ID, 'SUB_ID': 4,
            #'MESSAGE': 'イベント期間中はレアアイテムが特定楽曲で大量GET！$$「レアITEM」の表示をチェック！',
            'MESSAGE': 'イベント期間中はレアアイテムが特定楽曲で大量GET！$$毎週末に「レアITEM」の表示をチェック！',
            'BTN_FILE': 'btn_next.png', 'IMAGE_FILE': 'img_rule2_4.png',
            'BG_FILE': 'bg_live_1.png'
        }

    ]

    event_daily_entry = {
        'ID': EVENT_DAILY_ID, 'TITLE': 'EternalBIT', 'USER_DIV': 1, 'USER_REST': 0,
        'MUSIC_ID': 0, 'MUSIC_TYPE': -1, 'GROUP_ID': 3, 'PRIORITY': 2, 'TYPE': 5,
        'VALUE': 'item_table_4','TOP_ICON': 0, 'TIME_TABLE': 0, 'OPEN_MON': 0,
        'OPEN_TUE': 0, 'OPEN_WED': 0, 'OPEN_THU': 0, 'OPEN_FRI': 0, 'OPEN_SAT': 1,
        'OPEN_SUN': 1, 'START_YEAR': 0, 'START_MONTH': 0, 'START_DAY': 0, 'START_HOUR': 0,
        'START_MINUTE': 0, 'END_YEAR': 0, 'END_MONTH': 0, 'END_DAY': 0, 'END_HOUR': 0,
        'END_MINUTE': 0
    }

    top_banner_entry = {
        'ID': TOP_BANNER_ID, 'TEXT': 'EternalBIT', 'URL': 2000, 'URL_VALUE': BIT_EVENT_ID,
        'START_YEAR': 2025, 'START_MONTH': 1, 'START_DAY': 1, 'START_HOUR': 0,
        'START_MINUTE': 0, 'END_YEAR': 2038, 'END_MONTH': 1, 'END_DAY': 1, 'END_HOUR': 0,
        'END_MINUTE': 0
    }


    ################################################################################
    # Back to business!                                                            #
    ################################################################################
    # merge new data with original contents
    events_json.append(events_entry)
    event_exchange_json.append(event_exchange_entry)
    reward_main_json += reward_main_entries
    reward_personal_json += reward_personal_entries
    rule_json += rule_entries
    event_daily_json.append(event_daily_entry)
    top_banner_json.append(top_banner_entry)

    # replace files in output
    replacements = encrypt_replacements_json({
        'json/master_events.json': json.dumps(events_json),
        'json/master_event_exchange.json': json.dumps(event_exchange_json),
        'json/master_exchange_event_reward_main.json': json.dumps(reward_main_json),
        'json/master_exchange_event_reward_personal.json': json.dumps(reward_personal_json),
        'json/master_rule.json': json.dumps(rule_json),
        'json/master_event_daily.json': json.dumps(event_daily_json),
        'json/master_top_banner.json': json.dumps(top_banner_json)
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # copy banner images
    # (copy from exchange event 55)
    btn_event_top_bytes = read_file(resource_path, ver,
                                    'image/event/exchange/55/btn_event_top.png',
                                    zips=['1_pkg.zip'])
    replacements = {
        f'image/event/exchange/{BIT_EVENT_ID}/btn_event_top.png': btn_event_top_bytes,
        f'image/home/img_topbanner_{TOP_BANNER_ID}.png': btn_event_top_bytes
    }
    zip_path = path_join(resource_path, str(ver), '1_pkg.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python make_eternal_exchange_event.py <resource_path> <ver>')
        print('Example: python make_eternal_exchange_event.py res 732')
        exit()

    make_eternal_exchange_event(argv[1], int(argv[2]))
