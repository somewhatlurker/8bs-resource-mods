from enum import IntEnum, StrEnum
from typing import Union, get_args

class ItemCategory(IntEnum):  # inferred from image names, not comprehensive
    """Types of item used in presents."""
    MAIN = 0
    SUB = 1
    CHARA = 2
    EVENT = 3
    GACHATICKET = 4
    PLATE = 5

class MainItemId(IntEnum):  # ref: master_main_item.json
    """Items of MAIN type used in presents."""
    COINS = 1
    JEWELS_FREE = 2
    JEWELS_PAID = 3
    PREMIUM_TICKET = 4
    TICKET_COUNT = 5  # ???
    FRIEND_POINT = 6
    STORY_POINT = 7

    @staticmethod
    def category():
        return ItemCategory.MAIN

    @staticmethod
    def use_value():
        return True

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.COINS: 'コイン',
                self.JEWELS_FREE: 'コアジュエル',
                self.JEWELS_PAID: 'コアジュエル（有料）',
                self.PREMIUM_TICKET: 'プレミアムチケット',
                self.TICKET_COUNT: 'チケットカウント',
                self.FRIEND_POINT: '友情ポイント',
                self.STORY_POINT: 'ストーリーポイント'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.COINS: 'Coin',
                self.JEWELS_FREE: 'Core Jewel',
                self.JEWELS_PAID: 'Core Jewel (Paid)',
                self.PREMIUM_TICKET: 'Premium Ticket',
                self.TICKET_COUNT: 'Ticket Count',
                self.FRIEND_POINT: 'Friend Point',
                self.STORY_POINT: 'Story Point'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

class SubItemId(IntEnum):  # ref: master_sub_item.json
    """Items of SUB type used in presents."""
    EVO_ITEM_1STAR = 1
    EVO_ITEM_2STAR = 2
    EVO_ITEM_3STAR = 3
    EVO_ITEM_4STAR = 4
    EVO_ITEM_5STAR = 5
    ENERGY_UP_10 = 6
    ENERGY_UP_20 = 7
    ENERGY_UP_30 = 8
    LESSON_ITEM_1000 = 9
    LESSON_ITEM_3000 = 10
    LESSON_ITEM_9000 = 11
    LESSON_ITEM_15000 = 12
    SKILL_ITEM = 13
    SKILL_ITEM_PLUS = 14
    ROOM_EXPAND = 15
    UR_TICKET_MINI = 16
    LIMITBREAK_HINATA = 17
    LIMITBREAK_SUZUNE = 18
    LIMITBREAK_AKARI = 19
    LIMITBREAK_AYAME = 20
    LIMITBREAK_ANRI = 21
    LIMITBREAK_YUKINA = 22
    LIMITBREAK_HOTARU = 23
    LIMITBREAK_MEI = 24

    @staticmethod
    def category():
        return ItemCategory.SUB

    @staticmethod
    def use_value():
        return True

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.EVO_ITEM_1STAR: '音の種',
                self.EVO_ITEM_2STAR: '音の葉',
                self.EVO_ITEM_3STAR: '音の蕾',
                self.EVO_ITEM_4STAR: '音の花',
                self.EVO_ITEM_5STAR: '音の結晶',
                self.ENERGY_UP_10: 'エナジーブル Low',
                self.ENERGY_UP_20: 'エナジーブル High',
                self.ENERGY_UP_30: 'エナジーブル EX',
                self.LESSON_ITEM_1000: '強化プログラム C',
                self.LESSON_ITEM_3000: '強化プログラム B',
                self.LESSON_ITEM_9000: '強化プログラム A',
                self.LESSON_ITEM_15000: '強化プログラム S',
                self.SKILL_ITEM: 'スキルUPマイク',
                self.SKILL_ITEM_PLUS: 'スキルUPマイク+',
                self.ROOM_EXPAND: '部室増築',
                self.UR_TICKET_MINI: 'URチケットMini',
                self.LIMITBREAK_HINATA: '上限突破 Ver.ひなた',
                self.LIMITBREAK_SUZUNE: '上限突破 Ver.鈴音',
                self.LIMITBREAK_AKARI: '上限突破 Ver.月',
                self.LIMITBREAK_AYAME: '上限突破 Ver.彩芽',
                self.LIMITBREAK_ANRI: '上限突破 Ver.杏梨',
                self.LIMITBREAK_YUKINA: '上限突破 Ver.ゆきな',
                self.LIMITBREAK_HOTARU: '上限突破 Ver.ほたる',
                self.LIMITBREAK_MEI: '上限突破 Ver.メイ'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.EVO_ITEM_1STAR: 'Seed of Sound',
                self.EVO_ITEM_2STAR: 'Leaf of Sound',
                self.EVO_ITEM_3STAR: 'Bud of Sound',
                self.EVO_ITEM_4STAR: 'Flower of Sound',
                self.EVO_ITEM_5STAR: 'Crystal of Sound',
                self.ENERGY_UP_10: 'Energy Bull Low',
                self.ENERGY_UP_20: 'Energy Bull High',
                self.ENERGY_UP_30: 'Energy Bull EX',
                self.LESSON_ITEM_1000: 'Strength Program C',
                self.LESSON_ITEM_3000: 'Strength Program B',
                self.LESSON_ITEM_9000: 'Strength Program A',
                self.LESSON_ITEM_15000: 'Strength Program S',
                self.SKILL_ITEM: 'Skill Up Mic',
                self.SKILL_ITEM_PLUS: 'Skill Up Mic+',
                self.ROOM_EXPAND: 'Room Expansion',
                self.UR_TICKET_MINI: 'Mini UR Ticket',
                self.LIMITBREAK_HINATA: 'Lvl Limit Break (Hinata)',
                self.LIMITBREAK_SUZUNE: 'Lvl Limit Break (Suzune)',
                self.LIMITBREAK_AKARI: 'Lvl Limit Break (Akari)',
                self.LIMITBREAK_AYAME: 'Lvl Limit Break (Ayame)',
                self.LIMITBREAK_ANRI: 'Lvl Limit Break (Anri)',
                self.LIMITBREAK_YUKINA: 'Lvl Limit Break (Yukina)',
                self.LIMITBREAK_HOTARU: 'Lvl Limit Break (Hotaru)',
                self.LIMITBREAK_MEI: 'Lvl Limit Break (Mei)'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

class CharaItemId(IntEnum):
    """Placeholder for items of CHARA type used in presents.
    Real value should be stored in a separate integral field."""

    CHARA_ANY = 0

    @staticmethod
    def category():
        return ItemCategory.CHARA

    @staticmethod
    def use_value():
        return False

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.CHARA_ANY: '衣装'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.CHARA_ANY: 'Card'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

class EventItemId(IntEnum):
    """Placeholder for items of EVENT type used in presents.
    Real value should be stored in a separate integral field."""

    EVENT_ANY = 0

    @staticmethod
    def category():
        return ItemCategory.EVENT

    @staticmethod
    def use_value():
        return False

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.EVENT: 'イベントアイテム'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.EVENT: 'Event Item'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

class GachaTicketItemId(IntEnum):  # inferred from images
    """Items of GACHATICKET type used in presents."""
    SR_TICKET = 1
    UR_TICKET = 2
    SR_PLUS_TICKET = 3

    @staticmethod
    def category():
        return ItemCategory.GACHATICKET

    @staticmethod
    def use_value():
        return True

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.SR_TICKET: 'SRガチャチケット',
                self.UR_TICKET: 'URガチャチケット',
                self.SR_PLUS_TICKET: 'SRチケットPlus'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.SR_TICKET: 'SR Gacha Ticket',
                self.UR_TICKET: 'UR Gacha Ticket',
                self.SR_PLUS_TICKET: 'SR+ Gacha Ticket'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

class PlateItemId(IntEnum):
    """Placeholder for items of PLATE type used in presents.
    Real value should be stored in a separate integral field."""

    PLATE_ANY = 0

    @staticmethod
    def category():
        return ItemCategory.PLATE

    @staticmethod
    def use_value():
        return False

    def __str__(self):
        return f'{self.category().name}.{self.name}'

    def item_name(self, lang: str = 'ja'):
        if lang.lower() == 'ja':
            return {
                self.PLATE_ANY: 'ネームプレート'
            }.get(self)
        elif lang.lower() == 'en':
            return {
                self.PLATE_ANY: 'Nameplate'
            }.get(self)
        else:
            raise ValueError(f'Unsupported lang argument: {lang}.')

# must update helper(s) below and AnyItemIdType in db_models/util/db_enums if changed
AnyItemId = Union[
    MainItemId, SubItemId, CharaItemId, EventItemId, GachaTicketItemId, PlateItemId
]
AnyItemCategoryNameToEnum = {
        x.category().name: x for x in get_args(AnyItemId)
    }

def str_to_item_id(s: str) -> AnyItemId:
    """Convert from str(AnyItemId) back to AnyItemId object."""
    if type(s) in AnyItemId.__args__:
        return s
    if not isinstance(s, str):
        raise TypeError()

    s_split = s.split('.', 1)
    if len(s_split) == 1:
        raise ValueError('value does not contain ".".')

    code = s_split[0]
    name = s_split[1]

    etype = AnyItemCategoryNameToEnum.get(code)
    if etype is None:
        raise ValueError('Unrecognised discriminator code.')

    return etype[name]
