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
import random
from typing import List

import colorgram
from PIL import Image, ImageDraw, ImageFont

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, \
    set_card_names_from_master_chara, verify_gacha_data
from util import read_file, read_json_decrypted


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'

DEFAULT_BANNER_BG = 'bg_live_1'

BANNER_FONT_PATH = 'fonts/BIZ_UDPMincho/BIZUDPMincho-Bold.ttf'
BANNER_SMALL_FONT = ImageFont.truetype(BANNER_FONT_PATH, 16)
BANNER_MEDIUM_FONT = ImageFont.truetype(BANNER_FONT_PATH, 24)
BANNER_LARGE_FONT = ImageFont.truetype(BANNER_FONT_PATH, 40)

BANNER_TITLE_GRADIENT_COLOURS = (
    (255, 115, 20, 255), (255, 230, 20, 255), (255, 115, 20, 255)
)
BANNER_TITLE_INNER_STROKE_COLOUR = (255, 240, 210, 255)
BANNER_TITLE_INNER_STROKE_WIDTH = 4
BANNER_TITLE_OUTER_STROKE_WIDTH = 2
BANNER_TITLE_TOTAL_STROKE_WIDTH = BANNER_TITLE_INNER_STROKE_WIDTH + BANNER_TITLE_OUTER_STROKE_WIDTH
BANNER_TITLE_INNER_SHADOW_COLOUR = (8, 2, 0, 191)

BANNER_DESCRIPTION_BG_ALPHA = (0, 255, 255, 0)
BANNER_DESCRIPTION_STROKE_WIDTH = 2
BANNER_DESCRIPTION_TEXT_COLOUR = (255, 255, 255, 255)


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

def _draw_1px_horizontal_gradient(width, colours) -> Image:
    image = Image.new('RGBA', (width, 1), colours[0])
    if len(colours) == 1:
        return

    px_per_colour = width / (len(colours) - 1)

    pixels = image.load()
    for x in range(width):
        col_idx = int(x / px_per_colour)
        col_idx = min(len(colours) - 2, col_idx)
        progress = (x / px_per_colour) % 1
        col1_contrib = tuple(chan * (1 - progress) for chan in colours[col_idx])
        col2_contrib = tuple(chan * progress for chan in colours[col_idx + 1])
        col = tuple(int(col1_contrib[x] + col2_contrib[x]) for x in range(len(col1_contrib)))
        pixels[x, 0] = col

    return image

def _draw_vert_gradient_text(font, text, colours) -> Image:
    # size image by width of text being drawn and height of font from metrics
    # (use metrics so gradient scaling is consistent regardless of text)
    text_bbox = font.getbbox(text)
    font_metrics = font.getmetrics()
    image_size = (text_bbox[2], font_metrics[0] + font_metrics[1])

    # gradient image will be masked by text
    gradient_image = _draw_1px_vertical_gradient(image_size[1], colours)
    gradient_image = gradient_image.resize(image_size)

    # mask is just the text against an empty background
    mask_image = Image.new('RGBA', image_size)
    d = ImageDraw.Draw(mask_image)
    d.text((0, 0), text, font=font)

    # make a final output image, paste the masked gradient
    output_image = Image.new('RGBA', image_size)
    output_image.paste(gradient_image, mask=mask_image)

    return output_image


def _gen_premiumgacha_text_image(outline_colour) -> Image.Image:
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
        premium_pos[1] + premium_bbox[3] - gacha_bbox[3]
    )
    image_size = (
        gacha_pos[0] + gacha_bbox[2] + text_margin,
        gacha_pos[1] + gacha_bbox[3] + text_margin
    )

    # start by creating strokes for text
    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.text(
        premium_pos,
        'プレミアム',
        font=BANNER_LARGE_FONT,
        fill=outline_colour,
        stroke_fill=outline_colour,
        stroke_width=BANNER_TITLE_TOTAL_STROKE_WIDTH
    )
    d.text(
        gacha_pos,
        'ガチャ',
        font=BANNER_MEDIUM_FONT,
        fill=outline_colour,
        stroke_fill=outline_colour,
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
    for offset in range(-1, 2):
        d.text(
            (premium_pos[0] + offset, premium_pos[1] + offset),
            'プレミアム',
            font=BANNER_LARGE_FONT,
            fill=BANNER_TITLE_INNER_SHADOW_COLOUR
        )
        d.text(
            (gacha_pos[0] + offset, gacha_pos[1] + offset),
            'ガチャ',
            font=BANNER_MEDIUM_FONT,
            fill=BANNER_TITLE_INNER_SHADOW_COLOUR
        )
    # then create and composite the gradient text images
    premium_gradient_image = _draw_vert_gradient_text(BANNER_LARGE_FONT, 'プレミアム',
                                                      BANNER_TITLE_GRADIENT_COLOURS)
    gacha_gradient_image = _draw_vert_gradient_text(BANNER_MEDIUM_FONT, 'ガチャ',
                                                    BANNER_TITLE_GRADIENT_COLOURS)
    image.alpha_composite(premium_gradient_image, tuple(x - 1 for x in premium_pos))
    image.alpha_composite(gacha_gradient_image, tuple(x - 1 for x in gacha_pos))

    return image

def _gen_banner_text_image(text, bg_colour, outline_colour) -> Image.Image:
    """Create Image of banner text with stroke and background."""
    text_margin = BANNER_DESCRIPTION_STROKE_WIDTH

    lines = text.split('\n')
    # base metrics for first line
    text_bbox = BANNER_SMALL_FONT.getbbox(lines[0])
    text_pos = (text_margin, text_margin)
    image_size = [
        text_pos[0] + text_bbox[2] + text_margin,
        text_pos[1] + text_bbox[3] + text_margin
    ]
    # then adjust height and adjust width if necessary for each subsequent line
    font_metrics = BANNER_SMALL_FONT.getmetrics()
    font_height = font_metrics[0] + font_metrics[1]
    image_size[1] = len(lines) * (font_height + text_margin * 2)
    for line in lines[1:]:
        # image_size[1] += font_height + text_margin * 2
        line_bbox = BANNER_SMALL_FONT.getbbox(line)
        line_size_w = text_pos[0] + line_bbox[2] + text_margin
        if line_size_w > image_size[0]:
            image_size[0] = line_size_w

    # start by creating the background
    bg_colours = []
    for alpha in BANNER_DESCRIPTION_BG_ALPHA:
        if len(bg_colour) == 4:
            colour = bg_colour[:3] + (bg_colour[3] * alpha // 255,)
        else:
            colour = bg_colour + (alpha,)
        bg_colours.append(colour)
    bg_colours = tuple(bg_colours)
    bg_image = _draw_1px_horizontal_gradient(image_size[0], bg_colours)
    image = bg_image.resize(image_size)

    # then text stroke
    d = ImageDraw.Draw(image)
    d.text(
        text_pos,
        text,
        font=BANNER_SMALL_FONT,
        fill=outline_colour,
        stroke_fill=outline_colour,
        stroke_width=BANNER_DESCRIPTION_STROKE_WIDTH,
        spacing=0,
        align='center'
    )

    # and finally the main text
    d.text(
        text_pos,
        text,
        font=BANNER_SMALL_FONT,
        fill=BANNER_DESCRIPTION_TEXT_COLOUR,
        spacing=BANNER_DESCRIPTION_STROKE_WIDTH*2,
        align='center'
    )

    return image


def _gen_gacha_banner_image_internal(
        bg_name: str,
        card_image_files: List[str],
        description_text: str,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    if not bg_name:
        bg_name = DEFAULT_BANNER_BG
    # TODO: handle split bg
    if '/' in bg_name:
        bg_name = bg_name.split('/')[0]

    bg_bytes = read_file(resource_path, ver, f'image/bg/{bg_name}.png')
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

    # extract dominant colours (colorgram.py)
    dominant_colours = colorgram.extract(banner_image, 4)
    darkest_dominant_colour = dominant_colours[0]
    lightest_dominant_colour = dominant_colours[0]
    saturated_dominant_colour = dominant_colours[0]
    for colour in dominant_colours:
        if colour.hsl[2] < darkest_dominant_colour.hsl[2]:
            darkest_dominant_colour = colour
        if colour.hsl[2] > lightest_dominant_colour.hsl[2]:
            lightest_dominant_colour = colour
        if colour.hsl[1] > saturated_dominant_colour.hsl[1]:
            saturated_dominant_colour = colour

    # add card images
    card_image_bytes = [read_file(resource_path, ver, f) for f in card_image_files]
    card_images = [Image.open(BytesIO(b)) for b in card_image_bytes]
    for i, image in enumerate(card_images):
        image = image.convert('RGBA')
        scale_width = banner_image.height
        scale_height = image.height * scale_width // image.width
        image = image.resize((scale_width, scale_height))
        card_images[i] = image

    card_image_pos = []
    if len(card_images) >= 1:
        if len(card_images) < 3:
            card_image_pos.append((card_images[0].width // 8, 0))
        else:
            card_image_pos.append((-card_images[0].width // 6, 0))
    if len(card_images) >= 2:
        if len(card_images) < 4:
            card_image_pos.append((banner_image.width - card_images[1].width * 9 // 8, 0))
        else:
            card_image_pos.append((banner_image.width - card_images[1].width * 5 // 6, 0))
    if len(card_images) >= 3:
        card_image_pos.append((card_images[2].width // 2, 0))
    if len(card_images) >= 4:
        card_image_pos.append((banner_image.width - card_images[3].width * 3 // 2, 0))

    for i in range(len(card_image_pos)-1, -1, -1):
        banner_image.alpha_composite(card_images[i], card_image_pos[i])

    # add title text
    title_text = _gen_premiumgacha_text_image(saturated_dominant_colour.rgb + (220,))
    title_text_left = (banner_image.width - title_text.width) // 2
    if description_text:
        title_text_upper = (banner_image.height - title_text.height) * 5 // 6
    else:
        title_text_upper = (banner_image.height - title_text.height) * 4 // 6
    banner_image.alpha_composite(title_text, (title_text_left, title_text_upper))

    # add banner text
    if description_text:
        desc_text = _gen_banner_text_image(description_text,
                                           lightest_dominant_colour.rgb + (220,),
                                           darkest_dominant_colour.rgb + (255,))
        desc_text_left = (banner_image.width - desc_text.width) // 2
        desc_text_upper = (banner_image.height - desc_text.height) * 1 // 6
        banner_image.alpha_composite(desc_text, (desc_text_left, desc_text_upper))

    return banner_image

def gen_gacha_banner_image_ja(
        limited_gacha_data_dict: dict,
        output_gacha_id: int,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    if limited_gacha_data_dict:
        bg_name = limited_gacha_data_dict.get('BANNER_BG')
        image_cards = [card.id for card in limited_gacha_data_dict['CARDS']
                       if card.rarity == 4]
        description_text = limited_gacha_data_dict.get('BANNER_TEXT_JA')
    else:
        bg_name = None
        image_cards = []
        description_text = None

    # randomly remove some cards if more than four
    rd = random.Random(output_gacha_id)
    if len(image_cards) > 4:
        while len(image_cards) > 4:
            idx = rd.randrange(len(image_cards))
            del image_cards[idx]

    # then randomly shuffle them
    shuffled_image_cards = []
    while len(image_cards) > 0:
        idx = rd.randrange(len(image_cards))
        shuffled_image_cards.append(image_cards[idx])
        del image_cards[idx]

    return _gen_gacha_banner_image_internal(
        bg_name,
        [f'image/chara/stand/stand_chara{id}_2.png' for id in shuffled_image_cards],
        description_text,
        resource_path,
        ver
    )


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

    perm_banner_image = _gen_gacha_banner_image_internal(None, [], None,
                                                         resource_path, ver)
    perm_banner_image = perm_banner_image.convert('RGB').convert('P')
    perm_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')
    gacha_id += 1

    for banner in limited_gacha_data:
        lim_banner_image = gen_gacha_banner_image_ja(banner, gacha_id, resource_path, ver)
        lim_banner_image = lim_banner_image.convert('RGB').convert('P')
        lim_banner_image.save(f'gacha_banners/img_banner{gacha_id}.png')
        gacha_id += 1

    # print(limited_gacha_data)
    # print(permanent_gacha_data)

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver>')
        print('Example: python gen_gacha_rotation.py res 733')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]))
