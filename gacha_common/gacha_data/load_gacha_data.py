# helper module to load gacha data from csv, plus some useful stuff like relevant enums

import csv
from datetime import date
import re
from typing import Dict, List


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

CARD_NAME_REGEX = re.compile(r'^【(?P<series>.*)】(?P<chara>.*)')


class CardDetail:
    def __init__(
            self,
            chara: int,
            id: int,
            rarity: int,
            name: int | None,
            series: int | None,
            gacha_bg: str | None
        ):
        self.chara = chara
        self.id = id
        self.rarity = rarity
        self.name = name
        self.series = series
        self.gacha_bg = gacha_bg

    def __str__(self) -> str:
        return f'{RARITY_ID_TO_NAME(self.rarity)} {self.id}'

    def __repr__(self) -> str:
        return f'CardDetail({self.chara}, {self.id}, {self.rarity}, {self.name}, {self.series}, {self.gacha_bg})'

    def __eq__(self, other) -> bool:
        if not isinstance(other, CardDetail):
            return NotImplemented
        return self.id == other.id

    def get_chara_name(self) -> str:
        if not self.name:
            return None

        match = CARD_NAME_REGEX.match(self.name)
        return match.group('chara')

    def get_series_name(self) -> str:
        if not self.name:
            return None

        match = CARD_NAME_REGEX.match(self.name)
        return match.group('series')


def _load_gacha_data_csv(path: str) -> List[dict]:
    """Load a gacha data CSV file to list of dictionaries (one per series/banner).

    Output details:
      - Returns a list of series/banners
      - Each one may contain any combination of the following keys:
        - ISO_WEEK
        - DURATION_DAYS
        - EXPECT_START_DATE_EARLIEST
        - EXPECT_START_DATE_LATEST
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
            'Start Date (Earliest)': 'EXPECT_START_DATE_EARLIEST',
            'Start Date (Latest)': 'EXPECT_START_DATE_LATEST',
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
                card = CardDetail(chara_id, int(card_id), RARITY_NAME_TO_ID[rarity],
                                  None, None, None)
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
        - EXPECT_START_DATE_EARLIEST: str (MM/DD)
        - EXPECT_START_DATE_LATEST: str (MM/DD)
        - BANNER_TEXT_JA: str
        - BANNER_TEXT_EN: str
        - BANNER_BG: str
        - UR_DESC_TEXT_JA: str
        - UR_DESC_TEXT_EN: str
        - SR_DESC_TEXT_JA: str
        - SR_DESC_TEXT_EN: str
        - R_DESC_TEXT_JA: str
        - R_DESC_TEXT_EN: str
        - CARDS: List[CardDetail]
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


def set_card_names_from_master_chara(
        data: List[dict],
        master_chara: List[dict]
    ):
    """Set card name fields from data in master_chara.

    Only applies to cards that are in master_gacha; others are ignored.
    """
    master_chara_dict = {x['ID']: x for x in master_chara[1:]}
    for row in data:
        for card in row['CARDS']:
            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card: continue

            card.name = master_chara_card['NAME']

def set_card_series_from_master_chara(
        data: List[dict],
        master_chara: List[dict]
    ):
    """Set card series fields from data in master_chara.

    Only applies to cards that are in master_gacha; others are ignored.
    """
    master_chara_dict = {x['ID']: x for x in master_chara[1:]}
    for row in data:
        for card in row['CARDS']:
            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card: continue

            card.series = master_chara_card['SERIES']

def set_card_gacha_bg_from_master_chara(
        data: List[dict],
        master_chara: List[dict]
    ):
    """Set card gacha_bg fields from data in master_chara.

    Only applies to cards that are in master_gacha; others are ignored.
    """
    master_chara_dict = {x['ID']: x for x in master_chara[1:]}
    for row in data:
        for card in row['CARDS']:
            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card: continue

            card.gacha_bg = master_chara_card['BG']


def _verify_gacha_data_start_date_range(data: List[dict]):
    """Verify the expected start date range (earliest and latest dates, MM/YY).

    Done by checking that the EXPECT_START_DATE_EARLIEST/LATEST fields match with
    the dates of the set ISO_WEEK in years 2004 and 2010 respectively.
    (Adjusted to account for DATE_OFFSET)

    Raises ValueError if verification fails.
    """
    for row in data:
        if not 'ISO_WEEK' in row: continue
        if not 'EXPECT_START_DATE_EARLIEST' in row:
            raise ValueError('Missing expected start date (earliest), cannot verify.')
        if not 'EXPECT_START_DATE_LATEST' in row:
            raise ValueError('Missing expected start date (latest), cannot verify.')

        iso_week = row['ISO_WEEK']
        date_offset = row.get('DATE_OFFSET', 0)
        expect_start_date_earliest = row['EXPECT_START_DATE_EARLIEST']
        expect_start_date_latest = row['EXPECT_START_DATE_LATEST']

        if date_offset < 0 or date_offset > 6:
            raise ValueError(f'Invalid date offset {date_offset}. Expected 0-6.')

        # 2004 was a leap year starting on Thursday, giving the earliest possible date
        # for each ISO week.
        date_earliest = date.fromisocalendar(2004, iso_week, date_offset + 1)
        date_earliest_str = date_earliest.strftime('%m/%d')
        if expect_start_date_earliest != date_earliest_str:
            raise ValueError(
                'Incorrect expected start date (earliest). '
                f'{expect_start_date_earliest} != {date_earliest_str}'
            )

        # 2010 was a common year starting on Friday, giving the latest possible date
        # for each ISO week.
        date_latest = date.fromisocalendar(2010, iso_week, date_offset + 1)
        date_latest_str = date_latest.strftime('%m/%d')
        if expect_start_date_latest != date_latest_str:
            raise ValueError(
                'Incorrect expected start date (latest). '
                f'{expect_start_date_latest} != {date_latest_str}'
            )

def _verify_gacha_data_date_duration(data: List[dict]):
    """Verify the limited banner durations.

    Banners must last at least one day and end in the same ISO week they start in.

    Done by checking that the DURATION_DAYS field is greater than zero, and that
    DATE_OFFSET plus DURATION_DAYS is less than or equal to 7.

    Raises ValueError if verification fails.
    """
    for row in data:
        if not 'DURATION_DAYS' in row: continue

        duration = row['DURATION_DAYS']
        date_offset = row.get('DATE_OFFSET', 0)

        if not duration > 0:
            raise ValueError(f'Invalid duration {duration}. Cannot be less than one day.')

        if duration + date_offset > 7:
            raise ValueError(f'Banner does not end in same ISO week as it started in.')

def _verify_gacha_data_no_overlapping_date_ranges(data: List[dict]):
    """Verify that no limited banners overlap each other in the data.

    Done by searching for other banners with same ISO_WEEK and same or higher DATE_OFFSET.
    DURATION_DAYS of this banner must not exceed difference between offsets of banners.

    Raises ValueError if verification fails.
    """
    for i, row in enumerate(data):
        if not 'ISO_WEEK' in row: continue
        if not 'DURATION_DAYS' in row: continue

        iso_week = row['ISO_WEEK']
        duration = row['DURATION_DAYS']
        date_offset = row.get('DATE_OFFSET', 0)

        for other_row in data[i+1:]:
            if not 'ISO_WEEK' in other_row: continue
            if other_row['ISO_WEEK'] != iso_week: continue
            other_date_offset = other_row.get('DATE_OFFSET', 0)
            if other_date_offset < date_offset: continue

            if duration > other_date_offset - date_offset:
                raise ValueError(f'Overlapping banner date ranges in ISO week {iso_week}')

def _verify_gacha_data_rarity_sr_or_ur(data: List[dict]):
    """Verify that all limited banners cards are SR or UR rarity.

    Raises ValueError if verification fails.
    """
    allowed_rarities = (RARITY_NAME_TO_ID['SR'], RARITY_NAME_TO_ID['UR'])
    for row in data:
        for card in row['CARDS']:
            if card.rarity not in allowed_rarities:
                raise ValueError(f'Card {card.id} has disallowed rarity: {RARITY_ID_TO_NAME[card.rarity]}')

def _verify_gacha_data_no_duplicate_cards(data: List[dict]):
    """Verify that no card IDs appear twice in the data.

    Done by maintaining a set of all card IDs seen so far and throwing an error if current
    card is already in that set.

    Raises ValueError if verification fails.
    """
    seen_cards = set()

    for row in data:
        for card in row['CARDS']:
            if card.id in seen_cards:
                raise ValueError(f'Duplicate card ID: {card.id}')
            seen_cards.add(card.id)

def _verify_gacha_data_chara_and_rarity_against_game(
        data: List[dict],
        master_chara_dict: Dict[int, dict]
    ):
    """Verify that chara ID and rarity of cards in data matches master_chara.

    Raises ValueError if verification fails.
    """
    for row in data:
        for card in row['CARDS']:
            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card:
                raise ValueError(f'Card {card.id} not in master_chara')

            if card.chara != master_chara_card['NO']:
                raise ValueError(f'Wrong chara ID for card {card.id}')
            if card.rarity != master_chara_card['RARE']:
                raise ValueError(f'Wrong rarity for card {card.id}')

def _verify_gacha_data_series_name_in_banner_text_ja(
        data: List[dict],
        master_chara_dict: Dict[int, dict],
        master_series_dict: Dict[int, dict]
    ):
    """Verify that the name of each card, or its series, is in the banner text.

    Only considers the Japanese text.
    Series name may come from the card master_series instead, to account for series
    where each card has a different name (e.g. animal or star sign).

    Raises ValueError if verification fails.
    """
    for row in data:
        for card in row['CARDS']:
            series_name_from_card = card.get_series_name()
            if series_name_from_card:
                if f'「{series_name_from_card}」' in row['BANNER_TEXT_JA']: continue

            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card:
                raise ValueError(f'Card {card.id} not in master_chara')

            series = master_series_dict[master_chara_card['SERIES']]
            if f'「{series["NAME"]}」' in row['BANNER_TEXT_JA']: continue

            raise ValueError(f'Card {card.id} series missing in banner text')

def _verify_gacha_data_series_name_in_desc_text_ja(
        data: List[dict],
        master_chara_dict: Dict[int, dict],
        master_series_dict: Dict[int, dict]
    ):
    """Verify that the name of each card, or its series, is in the description text.

    Only considers the Japanese text.
    Only considers the description matching card rarity.
    Series name may come from the card master_series instead, to account for series
    where each card has a different name (e.g. animal or star sign).

    Raises ValueError if verification fails.
    """
    for row in data:
        for card in row['CARDS']:
            desc_field = f'{RARITY_ID_TO_NAME[card.rarity]}_DESC_TEXT_JA'

            series_name_from_card = card.get_series_name()
            if series_name_from_card:
                if f'【{series_name_from_card}】' in row[desc_field]: continue

            master_chara_card = master_chara_dict.get(card.id)
            if not master_chara_card:
                raise ValueError(f'Card {card.id} not in master_chara')

            series = master_series_dict[master_chara_card['SERIES']]
            if f'【{series["NAME"]}】' in row[desc_field]: continue

            raise ValueError(f'Card {card.id} series missing in description text')

def _verify_gacha_data_chara_name_in_desc_text_ja(
        data: List[dict],
        master_chara_dict: Dict[int, dict]
    ):
    """Verify that the card's character name is in the description text.

    Only considers the Japanese text.
    Only considers the description matching card rarity.

    Raises ValueError if verification fails.
    """
    for row in data:
        for card in row['CARDS']:
            desc_field = f'{RARITY_ID_TO_NAME[card.rarity]}_DESC_TEXT_JA'

            # special case for 8/pLanet!! members: allow "8/pLanet!!全メンバー" as description
            if card.chara < 9 and "8/pLanet!!全メンバー" in row[desc_field]: continue

            chara_name_from_card = card.get_chara_name()
            if chara_name_from_card:
                if chara_name_from_card in row[desc_field]: continue

            raise ValueError(f'Card {card.id} chara name missing in description text')

def _verify_gacha_data_no_missing_cards(
        data: List[dict],
        master_chara_dict: Dict[int, dict]
    ):
    """Verify that all expected cards from master_chara are present in the gacha data.

    Event/promo series and birthday cards are ignored.
    Cards below SR rarity are also ignored.
    """
    seen_cards = set()

    for row in data:
        for card in row['CARDS']:
            seen_cards.add(card.id)

    for card in master_chara_dict.values():
        # skip event/promo series
        if card['SERIES'] == 17: continue
        # skip birthday cards
        if '【お誕生日】' in card['NAME']: continue
        # skip below SR rarity
        if card['RARE'] < 3: continue
        # error if not in seen_cards
        if card['ID'] not in seen_cards:
            raise ValueError(f'Card {card["ID"]} missing from gacha data')

def _verify_gacha_data_no_event_or_birthday_cards(
        data: List[dict],
        master_chara_dict: Dict[int, dict]
    ):
    """Verify that no event or birthday cards are present in the gacha data."""
    seen_cards = set()

    for row in data:
        for card in row['CARDS']:
            seen_cards.add(card.id)

    for card in master_chara_dict.values():
        is_event_or_birthday = False
        # event/promo series
        if card['SERIES'] == 17: is_event_or_birthday = True
        # birthday cards
        if '【お誕生日】' in card['NAME']: is_event_or_birthday = True

        if is_event_or_birthday:
            if card['ID'] in seen_cards:
                raise ValueError(f'Event or birthday card {card["ID"]} in gacha data')

def _verify_limited_gacha_data(
        data: List[dict],
        master_chara: List[dict] | None = None,
        master_series: List[dict] | None = None
    ):
    """Verify all the limited-specific gacha data is complete and accurate.

    _verify_common_gacha_data should be called for the combined list of limited
    and permanent data after using _verify_limited_gacha_data.

    master_chara and master_series are optional parameters that use data from game files
    to perform additional checks.
    set_card_names_from_master_gacha should also be called first if using game data for
    additional checks.

    Checks perfomed:
      - the expected start date range is correct (earliest and latest dates, MM/YY)
      - limited banners must last at least one day
      - limited banners end in the same ISO week they start in
      - no limited banners overlap each other
      - all limited banners cards are SR or UR rarity
      - name of each card, or its series, is in the banner text (Japanese only,
          needs master_chara and master_series)

    Raises ValueError if verification fails.
    """
    _verify_gacha_data_start_date_range(data)
    _verify_gacha_data_date_duration(data)
    _verify_gacha_data_no_overlapping_date_ranges(data)
    _verify_gacha_data_rarity_sr_or_ur(data)

    if master_chara is not None:
        master_chara_dict = {x['ID']: x for x in master_chara[1:]}

        if master_series is not None:
            master_series_dict = {x['ID']: x for x in master_series[1:]}
            _verify_gacha_data_series_name_in_banner_text_ja(data, master_chara_dict,
                                                             master_series_dict)

def _verify_common_gacha_data(
        data: List[dict],
        master_chara: List[dict] | None = None,
        master_series: List[dict] | None = None
    ):
    """Verify all the common gacha data is complete and accurate.

    _verify_common_gacha_data should be called for the combined list of limited
    and permanent data after using _verify_limited_gacha_data.

    master_chara and master_series are optional parameters that use data from game files
    to perform additional checks.
    set_card_names_from_master_gacha should also be called first if using game data for
    additional checks.

    Checks perfomed:
      - no card IDs appear twice
      - chara ID and rarity of cards matches master_chara (needs master_chara)
      - all expected cards from master_chara are present (needs master_chara)
      - no event or birthday cards are present (needs master_chara)
      - card's character name is in the description text (Japanese only,
          needs master_chara)
      - name of each card, or its series, is in the description text (Japanese only,
          needs master_chara and master_series)

    Raises ValueError if verification fails.
    """
    _verify_gacha_data_no_duplicate_cards(data)

    if master_chara is not None:
        master_chara_dict = {x['ID']: x for x in master_chara[1:]}
        _verify_gacha_data_chara_and_rarity_against_game(data, master_chara_dict)
        _verify_gacha_data_no_missing_cards(data, master_chara_dict)
        _verify_gacha_data_no_event_or_birthday_cards(data, master_chara_dict)
        _verify_gacha_data_chara_name_in_desc_text_ja(data, master_chara_dict)

        if master_series is not None:
            master_series_dict = {x['ID']: x for x in master_series[1:]}
            _verify_gacha_data_series_name_in_desc_text_ja(data, master_chara_dict,
                                                           master_series_dict)

def verify_gacha_data(
        limited_data: List[dict],
        permanent_data: List[dict],
        master_chara: List[dict] | None = None,
        master_series: List[dict] | None = None
    ):
    """Verify that the gacha data is complete and accurate.

    master_chara and master_series are optional parameters that use data from game files
    to perform additional checks.
    set_card_names_from_master_gacha should also be called first if using game data for
    additional checks.

    Checks performed for limited rotation data:
      - the expected start date range is correct (earliest and latest dates, MM/YY)
      - limited banners must last at least one day
      - limited banners end in the same ISO week they start in
      - no limited banners overlap each other
      - all limited banners cards are SR or UR rarity
      - name of each card, or its series, is in the banner text (Japanese only,
          needs master_chara and master_series)

    Checks perfomed for all data:
      - no card IDs appear twice
      - chara ID and rarity of cards matches master_chara (needs master_chara)
      - all expected cards from master_chara are present (needs master_chara)
      - no event or birthday cards are present (needs master_chara)
      - card's character name is in the description text (Japanese only,
          needs master_chara)
      - name of each card, or its series, is in the description text (Japanese only,
          needs master_chara and master_series)

    Raises ValueError if verification fails.
    """
    _verify_limited_gacha_data(limited_data, master_chara, master_series)
    _verify_common_gacha_data(limited_data + permanent_data, master_chara, master_series)
