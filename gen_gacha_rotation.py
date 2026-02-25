# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from io import BytesIO
import json
from typing import List

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, verify_gacha_data
from util import read_file, read_json_decrypted


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'

DEFAULT_BANNER_BG = 'bg_live_1'
BANNER_FONT_PATH = font_manager.findfont(
    font_manager.FontProperties(family='Droid Sans Japanese')
)
BANNER_SMALL_FONT = ImageFont.truetype(BANNER_FONT_PATH, 12)
BANNER_MEDIUM_FONT = ImageFont.truetype(BANNER_FONT_PATH, 24)
BANNER_LARGE_FONT = ImageFont.truetype(BANNER_FONT_PATH, 40)

BANNER_TITLE_GRADIENT_COLOURS = (
    (255, 115, 20, 255), (255, 230, 20, 255), (255, 115, 20, 255)
)
BANNER_TITLE_INNER_STROKE_COLOUR = (255, 240, 210, 255)
BANNER_TITLE_INNER_STROKE_WIDTH = 3
BANNER_TITLE_OUTER_STROKE_WIDTH = 2
BANNER_TITLE_TOTAL_STROKE_WIDTH = BANNER_TITLE_INNER_STROKE_WIDTH + BANNER_TITLE_OUTER_STROKE_WIDTH
BANNER_TITLE_INNER_SHADOW_COLOR = (12, 2, 0, 100)


def _draw_1px_vertical_gradient(height, colours) -> Image:
    image = Image.new('RGBA', (1, height), colours[0])
    if len(colours) == 1:
        return

    px_per_colour = height / (len(colours) - 1)

    pixels = image.load()
    for y in range(height):
        col_idx = int(y / px_per_colour)
        col_idx = min(len(colours) - 2, col_idx)
        progress = (y / px_per_colour) % 1
        col1_contrib = tuple(chan * (1 - progress) for chan in colours[col_idx])
        col2_contrib = tuple(chan * progress for chan in colours[col_idx + 1])
        col = tuple(int(col1_contrib[x] + col2_contrib[x]) for x in range(len(col1_contrib)))
        pixels[0, y] = col

    return image

def _gen_premiumgacha_text_image(outline_color) -> Image.Image:
    """Create Image of "プレミアムガチャ" text with gradient fill and strokes."""
    premium_bbox = BANNER_LARGE_FONT.getbbox('プレミアム')
    gacha_bbox = BANNER_MEDIUM_FONT.getbbox('ガチャ')

    text_margin = BANNER_TITLE_TOTAL_STROKE_WIDTH
    premium_pos = (
        text_margin - premium_bbox[0],
        text_margin - premium_bbox[1]
    )
    gacha_pos = (
        premium_pos[0] + premium_bbox[2] + int(text_margin * 1.5),
        premium_bbox[3] - gacha_bbox[3]
    )
    image_size = (
        gacha_pos[0] + gacha_bbox[2] + text_margin,
        gacha_pos[1] + gacha_bbox[3] + text_margin
    )

    # gradient image will be masked by text in final image
    # prepare it and its mask now
    gradient_image = _draw_1px_vertical_gradient(image_size[1],
                                                BANNER_TITLE_GRADIENT_COLOURS)
    gradient_image = gradient_image.resize(image_size)

    gradient_mask_image = Image.new('RGBA', image_size)
    d = ImageDraw.Draw(gradient_mask_image)
    d.text(premium_pos, 'プレミアム', font=BANNER_LARGE_FONT)
    d.text(gacha_pos, 'ガチャ', font=BANNER_MEDIUM_FONT)

    # move onto the actual output image, start by creating strokes for text
    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.text(
        premium_pos,
        'プレミアム',
        font=BANNER_LARGE_FONT,
        fill=outline_color,
        stroke_fill=outline_color,
        stroke_width=BANNER_TITLE_TOTAL_STROKE_WIDTH
    )
    d.text(
        gacha_pos,
        'ガチャ',
        font=BANNER_MEDIUM_FONT,
        fill=outline_color,
        stroke_fill=outline_color,
        stroke_width=BANNER_TITLE_TOTAL_STROKE_WIDTH
    )
    d.text(
        premium_pos,
        'プレミアム',
        font=BANNER_LARGE_FONT,
        fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_width=BANNER_TITLE_INNER_STROKE_WIDTH
    )
    d.text(
        gacha_pos,
        'ガチャ',
        font=BANNER_MEDIUM_FONT,
        fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_width=BANNER_TITLE_INNER_STROKE_WIDTH
    )
    # then create the inner drop shadow
    d.text(
        (premium_pos[0] + 0.75, premium_pos[1] + 0.75),
        'プレミアム',
        font=BANNER_LARGE_FONT,
        fill=BANNER_TITLE_INNER_SHADOW_COLOR
    )
    d.text(
        (gacha_pos[0] + 0.75, gacha_pos[1] + 0.75),
        'ガチャ',
        font=BANNER_MEDIUM_FONT,
        fill=BANNER_TITLE_INNER_SHADOW_COLOR
    )
    d.text(
        (premium_pos[0], premium_pos[1] + 0.75),
        'プレミアム',
        font=BANNER_LARGE_FONT,
        fill=BANNER_TITLE_INNER_SHADOW_COLOR
    )
    d.text(
        (gacha_pos[0], gacha_pos[1] + 0.75),
        'ガチャ',
        font=BANNER_MEDIUM_FONT,
        fill=BANNER_TITLE_INNER_SHADOW_COLOR
    )
    # then paste the gradient with its mask
    image.paste(gradient_image, mask=gradient_mask_image)

    return image


def gen_gacha_banner_image(
        limited_gacha_data_dict: dict,
        permanent_gacha_data: List[dict],
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    bg_file = DEFAULT_BANNER_BG
    if limited_gacha_data_dict:
        bg_file = limited_gacha_data_dict.get('BANNER_BG', bg_file)

    bg_bytes = read_file(resource_path, ver, f'image/bg/{bg_file}.png')
    banner_image = Image.open(BytesIO(bg_bytes))
    # convert to RGBA because input may be indexed colour
    banner_image = banner_image.convert('RGBA')

    # crop to correct aspect ratio (same as 500x120 image)
    crop_width = banner_image.width
    crop_height = int(banner_image.width * (120 / 500))
    if (crop_height > banner_image.height):
        crop_width = int(banner_image.height * (500 / 120))
        crop_height = banner_image.height
    crop_left = (banner_image.width - crop_width) // 2
    crop_upper = (banner_image.height - crop_height) // 2
    banner_image = banner_image.crop(
        (crop_left, crop_upper, crop_left + crop_width, crop_upper + crop_height)
    )
    # resize to 500x120
    banner_image = banner_image.resize((500, 120))

    # TODO: extract dominant colours (colorgram.py)

    # TODO: add limited cards

    # add title text
    title_text = _gen_premiumgacha_text_image((0, 0, 0, 191))
    title_text_left = (banner_image.width - title_text.width) // 2
    title_text_upper = (banner_image.height - title_text.height) * 5 // 6
    banner_image.alpha_composite(title_text, (title_text_left, title_text_upper))

    # TODO: add banner text

    return banner_image


def gen_gacha_rotation(resource_path, ver):
    master_chara = read_json_decrypted(resource_path, ver, 'json/master_chara.json')
    master_chara = json.loads(master_chara)
    master_gacha_main = read_json_decrypted(resource_path, ver, 'json/master_gacha_main.json')
    master_gacha_main = json.loads(master_gacha_main)
    master_series = read_json_decrypted(resource_path, ver, 'json/master_series.json')
    master_series = json.loads(master_series)

    limited_gacha_data = load_and_parse_gacha_data_csv(LIMITED_CSV_PATH)
    permanent_gacha_data = load_and_parse_gacha_data_csv(PERMANENT_CSV_PATH)

    set_card_names_from_master_chara(limited_gacha_data, master_chara)
    set_card_names_from_master_chara(permanent_gacha_data, master_chara)

    verify_gacha_data(limited_gacha_data, permanent_gacha_data,
                      master_chara, master_series)

    gacha_id = max([row['ID'] for row in master_gacha_main[1:]]) + 1
    perm_banner_image = gen_gacha_banner_image(None, permanent_gacha_data, gacha_id,
                                               resource_path, ver)

    perm_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')
    print(limited_gacha_data)
    print(permanent_gacha_data)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver>')
        print('Example: python gen_gacha_rotation.py res 733')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]))
