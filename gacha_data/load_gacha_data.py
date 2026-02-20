# helper module to load gacha data from csv, plus some useful stuff like relevant enums

import csv
from typing import List


CHARA_NAME_EN_TO_ID = {
    'Hinata': 1,
    'Suzune': 2,
    'Akari': 3,
    'Ayame': 4,
    'Anri': 5,
    'Yukina': 6,
    'Hotaru': 7,
    'Mei': 8,
    'Headmistress': 9,
    'Kanade': 10,
    'Alumi': 11,
    'Mint': 12,
    'Amor': 13,
    'Cwellan': 14,
    'Bellum': 15,
}
CHARA_ID_TO_NAME_EN = {id: name for name, id in CHARA_NAME_EN_TO_ID.items()}

RARITY_NAME_TO_ID = {
    'N': 1,
    'R': 2,
    'SR': 3,
    'UR': 4
}
RARITY_ID_TO_NAME = {id: name for name, id in RARITY_NAME_TO_ID.items()}


class CardDetail:
    def __init__(self, chara: int, id: int, rarity: int):
        self.chara = chara
        self.id = id
        self.name = None  # set later
        self.rarity = rarity

    def __str__(self) -> str:
        return f'{RARITY_ID_TO_NAME(self.rarity)} {self.id}'

    def __repr__(self) -> str:
        return f'CardDetail({self.chara}, {self.id}, {self.rarity})'

    def get_series() -> str:
        if not self.name:
            return None


def _load_gacha_data_csv(path: str) -> List[dict]:
    """Load a gacha data CSV file to list of dictionaries (one per series/banner).

    Output details:
      - Returns a list of series/banners
      - Each one may contain any combination of the following keys:
        - ISO_WEEK
        - DURATION_DAYS
        - BANNER_TEXT_JA
        - BANNER_TEXT_EN
        - BANNER_BG
        - UR_DESC_TEXT_JA
        - UR_DESC_TEXT_EN
        - SR_DESC_TEXT_JA
        - SR_DESC_TEXT_EN
        - R_DESC_TEXT_JA
        - R_DESC_TEXT_EN
        - CARDS_HINATA
        - CARDS_SUZUNE
        - CARDS_AKARI
        - CARDS_AYAME
        - CARDS_ANRI
        - CARDS_YUKINA
        - CARDS_HOTARU
        - CARDS_MEI
        - CARDS_HEADMISTRESS
        - CARDS_KANADE
        - CARDS_ALUMI
        - CARDS_MINT
        - CARDS_AMOR
        - CARDS_CWELLAN
        - CARDS_BELLUM
      - Values are left as strings
      - Only keys with a value will be set
    """
    with open(path, newline='', encoding='utf-8') as f:
        # note: I chose to layout the spreadsheets as columnar data (personal preference
        # for manually editing timeline-like data), so don't use built-in header
        # processing or anything - instead, read to a transposed list of lists, then
        # we'll convert to dictionaries ourselves afterwards.
        reader = csv.reader(f)
        transposed = []

        for i, row in enumerate(reader):    # i: transposed col index
            if len(transposed) < len(row):
                transposed += [[] for _ in range(len(row) - len(transposed))]
            for j, cell in enumerate(row):  # j: transposed row index
                if len(transposed[j]) < i:
                    transposed[j] += [None for _ in range(i - len(transposed[j]))]
                transposed[j].append(cell)

        col_heading_to_name = {  # maps heading (in sheet) to field name (in code)
            'ISO Week Number': 'ISO_WEEK',
            'Length (Days)': 'DURATION_DAYS',
            'Banner Text (ja)': 'BANNER_TEXT_JA',
            'Banner Text (en)': 'BANNER_TEXT_EN',
            'Banner BG': 'BANNER_BG',
            'UR Description Text (ja)': 'UR_DESC_TEXT_JA',
            'UR Description Text (en)': 'UR_DESC_TEXT_EN',
            'SR Description Text (ja)': 'SR_DESC_TEXT_JA',
            'SR Description Text (en)': 'SR_DESC_TEXT_EN',
            'R Description Text (ja)': 'R_DESC_TEXT_JA',
            'R Description Text (en)': 'R_DESC_TEXT_EN',
        } | {chara: f'CARDS_{chara.upper()}' for chara in CHARA_NAME_EN_TO_ID.keys()}
        col_index_to_name = {}  # maps index to name (populated from first transposed row)
        for i, cell in enumerate(transposed[0]):
            if cell in col_heading_to_name:
                col_index_to_name[i] = col_heading_to_name[cell]
        del transposed[0]  # done with heading row now, so remove it

        # replace existing row lists with new dictionaries
        for i, row in enumerate(transposed):
            row_dict = {}
            for index, name in col_index_to_name.items():
                val = row[index]
                if val:
                    row_dict[name] = val
            transposed[i] = row_dict

        return transposed

def _parse_gacha_data_cards(data: List[dict]):
    """Replace the CARDS_* fields in gacha data with a single unified CARDS field.

    In addition, the string value is converted to a list of CardDetail entries.
    """
    fieldname_to_chara_id = \
        {f'CARDS_{chara.upper()}': id for chara, id in CHARA_NAME_EN_TO_ID.items()}
    for row in data:
        cards = []
        for field, chara_id in fieldname_to_chara_id.items():
            stringval = row.get(field)
            if not stringval: continue
            new_cards = [x.strip() for x in stringval.split(',')]
            for cardstr in new_cards:
                rarity, card_id = cardstr.split()
                card = CardDetail(chara_id, int(card_id), RARITY_NAME_TO_ID[rarity])
                cards.append(card)
            del row[field]
        row['CARDS'] = cards

def _parse_gacha_data_decimal_iso_weeknums(data: List[dict]):
    """Parse ISO_WEEK field (which may be decimal in raw data).

    Replaces it with integer ISO_WEEK and DATE_OFFSET columns.
    """
    for row in data:
        if not 'ISO_WEEK' in row: continue
        iso_week_float = float(row['ISO_WEEK'])
        iso_week_int = int(iso_week_float)
        iso_week_remainder = iso_week_float - iso_week_int
        row['ISO_WEEK'] = iso_week_int
        row['DATE_OFFSET'] = int(iso_week_remainder * 7)

def _parse_gacha_data_duration_days_int(data: List[dict]):
    """Parse DURATION_DAYS field to integer."""
    for row in data:
        if not 'DURATION_DAYS' in row: continue
        row['DURATION_DAYS'] = int(row['DURATION_DAYS'])

def load_and_parse_gacha_data_csv(path: str):
    """Load a gacha data CSV file to list of dictionaries (one per series/banner).

    Output details:
      - Returns a list of series/banners
      - Each one may contain any combination of the following keys:
        - ISO_WEEK: int
        - DATE_OFFSET: int
        - DURATION_DAYS: int
        - BANNER_TEXT_JA: str
        - BANNER_TEXT_EN: str
        - BANNER_BG: str
        - UR_DESC_TEXT_JA: str
        - UR_DESC_TEXT_EN: str
        - SR_DESC_TEXT_JA: str
        - SR_DESC_TEXT_EN: str
        - R_DESC_TEXT_JA: str
        - R_DESC_TEXT_EN: str
        - CARDS: CardDetail
      - Only keys with a value will be set
    """
    data = _load_gacha_data_csv(path)
    _parse_gacha_data_cards(data)
    _parse_gacha_data_decimal_iso_weeknums(data)
    _parse_gacha_data_duration_days_int(data)

    # remove rows with no cards,
    # use iteration by index to find and remove in one pass
    for i in range(len(data) - 1, -1, -1):
        if not data[i].get('CARDS'):
            del data[i]
    return data
