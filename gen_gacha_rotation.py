# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
import json
import math
from os.path import join as path_join
import random
from typing import Dict, List

from PIL import Image

from gacha_common.gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, set_card_series_from_master_chara, \
    set_card_gacha_bg_from_master_chara, verify_gacha_data
from gacha_common.gen_gacha_banner_image import gen_gacha_banner_image
from gacha_common.gen_gacha_description_text import \
    gen_gacha_description_text_combined
from gacha_common.gen_gacha_per_table import gen_gacha_per_table
from util import encrypt_replacements_json, read_json_decrypted, \
                 replace_files_in_ver, replace_files_in_zip


LIMITED_CSV_PATH = 'gacha_common/gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_common/gacha_data/permanent.csv'

PERMANENT_TOP_SCREEN_CARDS = [
    171, 172, 173, 174, 179, 180, 181, 182,  # 8/pLanet!! [Stage]
    473, 474,  # 2_wEi [Nightmare]
    666, 667, 668  # B.A.C [B.A.C]
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

ELEVEN_PULL_SR_GUARANTEE = True  # SR_SET

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

MONTHS_JA = {
    1: '1月',
    2: '2月',
    3: '3月',
    4: '4月',
    5: '5月',
    6: '6月',
    7: '7月',
    8: '8月',
    9: '9月',
    10: '10月',
    11: '11月',
    12: '12月'
}
MONTHS_EN = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec'
}

HTML_TABLE_STRINGS_JA = {
    'starts_on': 'Starts On',
    'weekday_after_date': '{weekday} after {date}',
    'date_format': '%m月%d日',
    'duration': 'Duration',
    'suffix_days': '日',
    'image': 'Image',
    'contents': 'Limited Cards'
}
HTML_TABLE_STRINGS_EN = {
    'starts_on': 'Starts On',
    'weekday_after_date': '{weekday} after {date}',
    'date_format': '%m/%d',
    'duration': 'Duration',
    'suffix_days': ' Days',
    'image': 'Image',
    'contents': 'Limited Cards'
}

HTML_BANNER_IMAGE_PATH = 'static/gacha/img_banner{id}.png'


def _gen_limited_gacha_banner_image_ja(
        limited_gacha_data_dict: dict | None,
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    # note: also works for permanent series, just provides nothing musch useful over
    # calling gen_gacha_banner_image directly
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
        permanent_gacha_data: List[dict],
        limited_gacha_data_dict: dict | None,
        first_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> dict:
    banner_image = _gen_limited_gacha_banner_image_ja(limited_gacha_data_dict,
                                                      first_gacha_id, resource_path, ver)
    banner_image = banner_image.quantize()
    # banner_image.save(f'gacha_banners/img_banner{first_gacha_id}.png')

    desc_text = gen_gacha_description_text_combined(permanent_gacha_data,
                                                    limited_gacha_data_dict, GACHA_ODDS,
                                                    ELEVEN_PULL_SR_GUARANTEE)
    # with open(f'gacha_banners/banner{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     f.write(desc_text)

    perm_contents_text_ja = _gacha_short_contents_text(permanent_gacha_data, None,
                                                       GACHA_ODDS, 'ja')
    perm_contents_text_en = _gacha_short_contents_text(permanent_gacha_data, None,
                                                       GACHA_ODDS, 'en')
    limited_contents_text_ja = _gacha_short_contents_text([], limited_gacha_data_dict,
                                                          GACHA_ODDS, 'ja')
    limited_contents_text_en = _gacha_short_contents_text([], limited_gacha_data_dict,
                                                          GACHA_ODDS, 'en')

    per_table = gen_gacha_per_table(permanent_gacha_data, limited_gacha_data_dict,
                                    GACHA_ODDS)
    # with open(f'gacha_banners/table{first_gacha_id}.txt', 'w', encoding='utf-8') as f:
    #     json.dump(per_table, f)

    print(f'Gacha entry generated, id={first_gacha_id}')

    return {
        'first_gacha_id': first_gacha_id,
        'banner_image': banner_image,
        'desc_text': desc_text,
        'per_table': per_table,
        'limited_data': limited_gacha_data_dict,
        'perm_contents_text_ja': perm_contents_text_ja,
        'perm_contents_text_en': perm_contents_text_en,
        'limited_contents_text_ja': limited_contents_text_ja,
        'limited_contents_text_en': limited_contents_text_en
    }

def _master_gacha_row(entry: dict, gacha_id: int, year: int) -> dict:
    limited_data = entry.get('limited_data')
    if limited_data:
        iso_week = limited_data['ISO_WEEK']
        duration = limited_data['DURATION_DAYS']
        date_offset = limited_data.get('DATE_OFFSET', 0)

        start_date = date.fromisocalendar(year, iso_week, date_offset + 1)
        # note: end_date is day *after* end, not day of end
        end_date = start_date + timedelta(days=duration)
    else:
        start_date = None
        end_date = None

    desc_text = entry['desc_text'].replace('\n', '$')
    if start_date:
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
        'GACHA_TYPE': 0,  # regular premium gacha
        'NAME': 'プレミアムガチャ',
        'ORDER': 1,  # seems to be based on type
        'BANNER': f'img_banner{entry["first_gacha_id"]}',
        'DETAIL': desc_text,
        'USE_ITEM': 2,  # jewels
        'GACHA_1': 25,  # don't chang costs -- image assets have value hardcoded
        'GACHA_10': 0,
        'GACHA_11': 250,
        'SR_SET': 1 if ELEVEN_PULL_SR_GUARANTEE else 0,
        'SHEET': f'gacha_detail{entry["first_gacha_id"]}',
        'SHEET_DAILY': f'gacha_detail{entry["first_gacha_id"]}',  # just reuse same sheet
        'FROM_INSTALL': 0,
        'START_YEAR': start_date.year if start_date else 0,
        'START_MONTH': start_date.month if start_date else 0,
        'START_DAY': start_date.day if start_date else 0,
        'START_HOUR': 0,
        'START_MINUTE': 0,
        'END_YEAR': end_date.year if end_date else 0,
        'END_MONTH': end_date.month if end_date else 0,
        'END_DAY': end_date.day if end_date else 0,
        'END_HOUR': 0,
        'END_MINUTE': 0
    }

def _gen_limited_html_table(
        entries: List[dict],
        strings: Dict[str, str],
        months: Dict[int, str],
        weekdays: Dict[int, str],
        contents_key: str,
        indent: str='    '
    ) -> str:
    def limited_data_start_date_earliest(limited_data: dict):
        iso_week = limited_data['ISO_WEEK']
        duration = limited_data['DURATION_DAYS']
        date_offset = limited_data.get('DATE_OFFSET', 0)

        # 2004 was a leap year starting on Thursday, giving the earliest possible date
        # for each ISO week.
        return date.fromisocalendar(2004, iso_week, date_offset + 1)

    def limited_data_end_date_latest(limited_data: dict):
        iso_week = limited_data['ISO_WEEK']
        duration = limited_data['DURATION_DAYS']
        date_offset = limited_data.get('DATE_OFFSET', 0)

        # 2010 was a common year starting on Friday, giving the latest possible date
        # for each ISO week.
        start_date_latest = date.fromisocalendar(2010, iso_week, date_offset + 1)
        return start_date_latest + timedelta(days=date_offset)

    def entry_is_fully_in_month(entry: dict, month: int):
        limited_data = entry['limited_data']  # must have for this, exception is fine
        iso_week = limited_data['ISO_WEEK']
        duration = limited_data['DURATION_DAYS']
        date_offset = limited_data.get('DATE_OFFSET', 0)

        start_date_earliest = limited_data_start_date_earliest(limited_data)
        end_date_latest = limited_data_end_date_latest(limited_data)

        return start_date_earliest.month == month and end_date_latest.month == month

    output = '<table>\n'
    output += indent + '<tr>\n'
    output += indent*2 + '<th class="month-header"></th>\n'
    output += indent*2 + f'<th>{strings.get("starts_on")}</th>\n'
    output += indent*2 + f'<th>{strings.get("duration")}</th>\n'
    output += indent*2 + f'<th>{strings.get("image")}</th>\n'
    output += indent*2 + f'<th>{strings.get("contents")}</th>\n'
    output += indent + '</tr>\n'

    month_headers_until = 0   # how many entries already have their month header done
                              # (i.e. don't need to create one)
    alt_colour_class = False  # simple flag for whether to output with alt bg class

    for i, entry in enumerate(entries):
        limited_data = entry.get('limited_data')
        if not limited_data:
            month_headers_until += 1  # no row, so no month
            continue

        start_month = limited_data_start_date_earliest(limited_data).month
        end_month = limited_data_end_date_latest(limited_data).month

        output += indent + '<tr>\n'

        # make new month headers if necessary
        # two types of cell:
        #   - transitional: spans multiple rows, transitions from one row colour to next
        #        (used for rows that may span multiple months)
        #   - standard: spans multiple rows, single solid colour
        #        (used for rows that are completely within a single month)
        if i >= month_headers_until:
            is_standard = entry_is_fully_in_month(entry, start_month)

            span = 1
            for sub in entries[i+1:]:
                if is_standard and entry_is_fully_in_month(sub, start_month):
                    span += 1
                elif not is_standard and not entry_is_fully_in_month(sub, end_month):
                    span += 1
                else:
                    break

            if is_standard:
                colour_cls = 'row-color-alt' if alt_colour_class else 'row-color-main'
                month_cls = f'month {colour_cls}'
                month_text = months.get(start_month)
                month_cell = f'<th class="{month_cls}" rowspan="{span}">{month_text}</td>'
            else:
                colour_cls = 'row-trans-main' if alt_colour_class else 'row-trans-alt'
                month_cls = f'month {colour_cls}'
                month_cell = f'<th class="{month_cls}" rowspan="{span}"></td>'

            month_cell = indent*2 + month_cell + '\n'
            month_headers_until = i + span
            alt_colour_class = not alt_colour_class
        else:
            month_cell = ''

        start_date_approx = limited_data_start_date_earliest(limited_data)
        weekday = weekdays.get(limited_data.get('DATE_OFFSET', 0))
        date_str = start_date_approx.strftime(strings.get('date_format'))
        starts_on_text = strings.get('weekday_after_date').format(weekday=weekday,
                                                                  date=date_str)
        starts_on_attrs = f'data-iso-week="{limited_data["ISO_WEEK"]}"'
        starts_on_attrs += f' data-date-offset="{limited_data.get("DATE_OFFSET", 0)}"'
        starts_on_cell = f'<td {starts_on_attrs}>{starts_on_text}</td>'
        starts_on_cell = indent*2 + starts_on_cell + '\n'

        duration_days = limited_data.get('DURATION_DAYS', 0)
        duration_text = str(duration_days) + strings.get('suffix_days')
        duration_cell = f'<td>{duration_text}</td>'
        duration_cell = indent*2 + duration_cell + '\n'

        image_path = HTML_BANNER_IMAGE_PATH.format(id=entry["first_gacha_id"])
        image_tag = f'<img src="{image_path}" width=250 height=60 />'
        image_tag = indent*3 + image_tag + '\n'
        image_cell = indent*2 + '<td>\n' + image_tag + indent*2 + '</td>\n'

        contents_text = entry.get(contents_key)
        contents_text = contents_text.replace('\n', '<br>')
        contents_cell = f'<td>{contents_text}</td>'
        contents_cell = indent*2 + contents_cell + '\n'

        output += month_cell
        output += starts_on_cell
        output += duration_cell
        output += image_cell
        output += contents_cell
        output += indent + '</tr>\n'

    output += '</table>'
    return output

def _gen_markdown_page_en(
        permanent_gacha_entry: dict,
        limited_gacha_unique_entires: List[dict]
    ) -> str:
    output = '# Gacha Timetable\n\n'

    output += '## Permanent Gacha\n'
    output += 'These cards are always available, '
    output += 'regardless of whether there is a limited banner or not.\n\n'
    image_path = HTML_BANNER_IMAGE_PATH.format(id=permanent_gacha_entry["first_gacha_id"])
    output += f'![permanent gacha banner image]({image_path})\n\n'
    contents_text = permanent_gacha_entry.get('perm_contents_text_en')
    contents_text = contents_text.replace('\n', '<br>')
    output += contents_text + '\n\n'

    output += '## Limited Gacha\n'
    output += 'These cards are only available for a short time during the set period.\n\n'
    output += _gen_limited_html_table(limited_gacha_unique_entires, HTML_TABLE_STRINGS_EN,
                                      MONTHS_EN, WEEKDAYS_EN, 'limited_contents_text_en')

    return output


def gen_gacha_rotation(resource_path, ver, start_year, end_year):
    master_chara = read_json_decrypted(resource_path, ver, 'json/master_chara.json')
    master_chara = json.loads(master_chara)
    master_gacha_main = read_json_decrypted(resource_path, ver, 'json/master_gacha_main.json')
    master_gacha_main = json.loads(master_gacha_main)
    master_gacha_detail0 = read_json_decrypted(resource_path, ver, 'json/master_gacha_detail0.json')
    master_gacha_detail0 = json.loads(master_gacha_detail0)
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
    first_gacha_id = gacha_id  # first occurence of each entry

    permanent_gacha_entry = _gacha_list_entry(permanent_gacha_data, None, first_gacha_id,
                                              resource_path, ver)
    first_gacha_id += 1

    # add TOP screen cards for permanent_gacha_entry manually
    for row in permanent_gacha_entry['per_table']:
        if row['ID'] in PERMANENT_TOP_SCREEN_CARDS:
            row['TOP'] = 1

    limited_gacha_unique_entires = []
    for banner in limited_gacha_data:
        entry = _gacha_list_entry(permanent_gacha_data, banner, first_gacha_id,
                                  resource_path, ver)
        limited_gacha_unique_entires.append(entry)
        first_gacha_id += 1

    # print(permanent_gacha_entry)
    # print(limited_gacha_unique_entires)

    master_gacha_rows = []
    master_gacha_rows.append(
        _master_gacha_row(permanent_gacha_entry, gacha_id, start_year)
    )
    gacha_id += 1

    for year in range(start_year, end_year + 1):
        for entry in limited_gacha_unique_entires:
            master_gacha_rows.append(_master_gacha_row(entry, gacha_id, year))
            gacha_id += 1

    # print(master_gacha_rows)


    # output markdown page and web images
    md = _gen_markdown_page_en(permanent_gacha_entry, limited_gacha_unique_entires)
    with open(f'gacha_md/index.md', 'w', encoding='utf-8') as f:
        f.write(md)

    for entry in [permanent_gacha_entry] + limited_gacha_unique_entires:
        first_id = entry['first_gacha_id']
        entry['banner_image'].save(f'gacha_md/static/gacha/img_banner{first_id}.png')


    # add gacha detail sheets to ver
    replacements = {}
    for entry in [permanent_gacha_entry] + limited_gacha_unique_entires:
        header_row = master_gacha_detail0[0]
        full_table = [header_row] + entry['per_table']
        first_id = entry["first_gacha_id"]
        replacements[f'json/master_gacha_detail{first_id}.json'] = json.dumps(full_table)
    replacements = encrypt_replacements_json(replacements)
    zip_path = path_join(resource_path, str(ver), '1_json01.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

    # merge and replace master_gacha_main
    master_gacha_main.extend(master_gacha_rows)
    replacements = encrypt_replacements_json({
        'json/master_gacha_main.json': json.dumps(master_gacha_main)
    })
    replace_files_in_ver(resource_path, ver, replacements)

    # add images to ver
    replacements = {}
    for entry in [permanent_gacha_entry] + limited_gacha_unique_entires:
        io = BytesIO()
        entry['banner_image'].save(io, format='PNG')
        first_id = entry["first_gacha_id"]
        replacements[f'image/gacha/img_banner{first_id}.png'] = io.getvalue()
    zip_path = path_join(resource_path, str(ver), '1_pkg.zip')
    replace_files_in_zip(zip_path, replacements, if_exists=False)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 5:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver> <start_year> <end_year>')
        print('Example: python gen_gacha_rotation.py res 733 2026 2031')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]), int(argv[3]), int(argv[4]))
