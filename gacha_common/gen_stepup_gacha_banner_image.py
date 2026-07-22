from colorsys import hls_to_rgb
from io import BytesIO
import math
import random
from typing import List

import colorgram
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from util import read_file


DEFAULT_BANNER_BG = 'bg_live_1'

# fills entire image
BANNER_BG_SIZE = (960, 320)
BANNER_BG_Y = 0

BANNER_TITLE_FONT_PATH = 'fonts/Yusei_Magic/YuseiMagic-Regular.ttf'
BANNER_DESC_FONT_PATH = 'fonts/IBM_Plex_Sans_JP/IBMPlexSansJP-SemiBold.ttf'
BANNER_TITLE_FONT = ImageFont.truetype(BANNER_TITLE_FONT_PATH, 72)
BANNER_DESC_FONT = ImageFont.truetype(BANNER_DESC_FONT_PATH, 36)

BANNER_TITLE_COLOUR = (254, 244, 177, 255)
BANNER_TITLE_INNER_STROKE_COLOUR = (205, 50, 100, 255)
BANNER_TITLE_INNER_STROKE_WIDTH = 5
BANNER_TITLE_SHADOW_OFFSET = 5
BANNER_TITLE_OUTER_STROKE_COLOUR = (255, 255, 255, 255)
BANNER_TITLE_OUTER_STROKE_WIDTH = 6
BANNER_TITLE_TOTAL_STROKE_WIDTH = BANNER_TITLE_INNER_STROKE_WIDTH + BANNER_TITLE_OUTER_STROKE_WIDTH
BANNER_TITLE_SCALE_FACTOR = 2.2

BANNER_DESCRIPTION_BG_COLOUR = (245, 71, 150, 160)
BANNER_DESCRIPTION_BG_STROKE_COLOUR = (24, 8, 8, 160)
BANNER_DESCRIPTION_BG_STROKE_WIDTH = 2
BANNER_DESCRIPTION_BG_RADIUS = 6
BANNER_DESCRIPTION_TEXT_COLOUR = (250, 250, 0, 255)
BANNER_DESCRIPTION_TEXT_STROKE_COLOUR = (140, 0, 160, 255)
BANNER_DESCRIPTION_TEXT_STROKE_WIDTH = 4
BANNER_DESCRIPTION_TEXT_SHADOW_OFFSET = 4
BANNER_DESCRIPTION_TEXT_SHADOW_COLOUR = (0, 0, 0, 127)
BANNER_DESCRIPTION_SPACE_QUOTES = False


def _gen_gacha_title_text_image(title, shadow_colour) -> Image.Image:
    """Create Image of title (e.g. "ステップアップガチャ") text with fill, strokes, and shadow.
    """
    title_bbox = BANNER_TITLE_FONT.getbbox(title)

    text_margin = math.ceil(BANNER_TITLE_INNER_STROKE_WIDTH
                            + BANNER_TITLE_SHADOW_OFFSET
                            + BANNER_TITLE_OUTER_STROKE_WIDTH)
    title_pos = (
        text_margin - title_bbox[0],
        text_margin - title_bbox[1]
    )
    image_size = (
        title_pos[0] + title_bbox[2] + text_margin,
        title_pos[1] + title_bbox[3] + text_margin
    )

    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    # start by creating outer stroke
    for offset in range(BANNER_TITLE_SHADOW_OFFSET + 1):
        d.text(
            (title_pos[0] + offset, title_pos[1] + offset),
            title,
            font=BANNER_TITLE_FONT,
            fill=BANNER_TITLE_OUTER_STROKE_COLOUR,
            stroke_fill=BANNER_TITLE_OUTER_STROKE_COLOUR,
            stroke_width=BANNER_TITLE_TOTAL_STROKE_WIDTH
        )
    # then the shadow
        d.text(
            (
                title_pos[0] + BANNER_TITLE_SHADOW_OFFSET,
                title_pos[1] + BANNER_TITLE_SHADOW_OFFSET
            ),
            title,
            font=BANNER_TITLE_FONT,
            fill=shadow_colour,
            stroke_fill=shadow_colour,
            stroke_width=BANNER_TITLE_INNER_STROKE_WIDTH
        )
    # then inner stroke
    d.text(
        title_pos,
        title,
        font=BANNER_TITLE_FONT,
        fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_fill=BANNER_TITLE_INNER_STROKE_COLOUR,
        stroke_width=BANNER_TITLE_INNER_STROKE_WIDTH
    )
    # then actual text
    d.text(
        title_pos,
        title,
        font=BANNER_TITLE_FONT,
        fill=BANNER_TITLE_COLOUR
    )

    # rotate the image
    max_angle = math.degrees(math.asin(23 * BANNER_TITLE_SCALE_FACTOR / image.width))
    angle = min(3.3, max_angle)
    image = image.rotate(angle, Image.Resampling.BILINEAR, expand=True)

    return image.resize((
        int(image.width / BANNER_TITLE_SCALE_FACTOR),
        int(image.height / BANNER_TITLE_SCALE_FACTOR)
    ))

def _gen_banner_desc_text_image(text) -> Image.Image:
    """Create Image of banner description text with stroke and background."""
    text_margin = math.ceil(BANNER_DESCRIPTION_BG_STROKE_WIDTH) + \
                  math.ceil(BANNER_DESCRIPTION_TEXT_STROKE_WIDTH) + 5

    if BANNER_DESCRIPTION_SPACE_QUOTES:
        # hacky fix to make some proportional fonts look better
        text = text.replace('「', ' 「').replace('」', '」 ')
        text = text.replace('『', ' 『').replace('』', '』 ')
    lines = text.split('\n')
    # base metrics for first line
    text_bbox = BANNER_DESC_FONT.getbbox(lines[0])
    text_pos = (text_margin, text_margin - text_bbox[1])
    image_size = [
        text_pos[0] + text_bbox[2] + text_margin,
        text_pos[1] + text_bbox[3] + text_margin
    ]
    # then adjust height and adjust width if necessary for each subsequent line
    font_metrics = BANNER_DESC_FONT.getmetrics()
    font_height = font_metrics[0] + font_metrics[1]
    # image_size[1] = font_height + BANNER_DESCRIPTION_TEXT_STROKE_WIDTH * 2
    line_top = text_pos[1]
    for line in lines[1:]:
        # not sure if this is right for line height, but it's close enough
        line_top += font_metrics[0] + BANNER_DESCRIPTION_TEXT_STROKE_WIDTH * 2
        line_bbox = BANNER_DESC_FONT.getbbox(line)
        image_size[1] = line_top + line_bbox[3] + text_margin
        line_size_w = text_pos[0] + line_bbox[2] + text_margin
        if line_size_w > image_size[0]:
            image_size[0] = line_size_w
    image_size[1] = math.ceil(image_size[1])

    # start by creating the background
    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle(
        ((0, 0), (image_size[0] - 1, image_size[1] - 1)),
        radius=BANNER_DESCRIPTION_BG_RADIUS,
        fill=BANNER_DESCRIPTION_BG_COLOUR,
        outline=BANNER_DESCRIPTION_BG_STROKE_COLOUR,
        width=BANNER_DESCRIPTION_BG_STROKE_WIDTH
    )
    # then text shadow
    d.text(
        (
            text_pos[0] + BANNER_DESCRIPTION_TEXT_SHADOW_OFFSET,
            text_pos[1] + BANNER_DESCRIPTION_TEXT_SHADOW_OFFSET
        ),
        text,
        font=BANNER_DESC_FONT,
        fill=BANNER_DESCRIPTION_TEXT_SHADOW_COLOUR,
        spacing=BANNER_DESCRIPTION_TEXT_STROKE_WIDTH*2,
        align='right'
    )
    # then text stroke
    d.text(
        text_pos,
        text,
        font=BANNER_DESC_FONT,
        fill=BANNER_DESCRIPTION_TEXT_STROKE_COLOUR,
        stroke_fill=BANNER_DESCRIPTION_TEXT_STROKE_COLOUR,
        stroke_width=BANNER_DESCRIPTION_TEXT_STROKE_WIDTH,
        spacing=0,
        align='right'
    )
    # and finally the main text
    d.text(
        text_pos,
        text,
        font=BANNER_DESC_FONT,
        fill=BANNER_DESCRIPTION_TEXT_COLOUR,
        spacing=BANNER_DESCRIPTION_TEXT_STROKE_WIDTH*2,
        align='right'
    )

    return image


def _load_bg_image(bg_io):
    """Load, crop, and resize bg image to BANNER_BG_SIZE resolution RGBA.

    Input is a file-like IO object.
    """
    image = Image.open(bg_io)
    # convert to RGBA because input may be indexed colour
    image = image.convert('RGBA')

    w = BANNER_BG_SIZE[0]
    h = BANNER_BG_SIZE[1]

    # crop to correct aspect ratio (same as output)
    crop_width = image.width
    crop_height = int(image.width * (h / w))
    if (crop_height > image.height):
        crop_width = int(image.height * (w / h))
        crop_height = image.height
    crop_left = (image.width - crop_width) // 2
    crop_upper = (image.height - crop_height) // 2
    image = image.crop(
        (crop_left, crop_upper, crop_left + crop_width, crop_upper + crop_height)
    )
    # resize
    image = image.resize((w, h))

    return image

def _split_bg_image_mask(size, split_pos, angle):
    """Generates a mask for split background so only the right side is visible.

    - size is (width, height)
    - split_pos sets the position in pixels from the left edge
    - angle sets the angle of the split in degrees from vertical (positive=slant to right)
    """
    # compute constants
    # (note: use pixel centres for calculation, so total distance is one less than height)
    x_offset_per_y = math.tan(math.radians(angle))
    x_offset_top = x_offset_per_y * (size[1] - 1) / 2
    x_offset_top += split_pos * size[0]

    # start with an empty background
    mask_image = Image.new('RGBA', size)

    pixels = mask_image.load()
    for y in range(size[1]):
        x_offset = x_offset_top - y * x_offset_per_y
        if x_offset >= size[0]: continue  # no pixels to fill on this line
        if x_offset < 0: x_offset = 0

        # partially fill left-most pixel based on coverage
        cov = 1 - (x_offset % 1)
        pixels[int(x_offset), y] = (0, 0, 0, int(255 * cov))

        # completely fill rest of row
        for x in range(math.ceil(x_offset), size[0]):
            pixels[x, y] = (0, 0, 0, 255)

    return mask_image

def _clamp_colour_lightness(colour: colorgram.Color, min: int, max: int) -> colorgram.Color:
    """Clamps lightness of colour to be within given range (inclusive)."""
    if colour.hsl.l < min:
        l = min
    elif colour.hsl.l > max:
        l = max
    else:
        return colour

    # note: confirmed that colorsys hls is equal to colorgram hsl
    # (except for potential rounding differences, but they're not too important)
    hls = (
        colour.hsl.h / 255,
        l / 255,
        colour.hsl.s / 255
    )
    rgb = tuple(int(x * 255) for x in hls_to_rgb(*hls))
    proportion = colour.proportion
    return colorgram.Color(*rgb, proportion)

def _clamp_colour_sat(colour: colorgram.Color, min: int, max: int) -> colorgram.Color:
    """Clamps saturation of colour to be within given range (inclusive)."""
    if colour.hsl.s < min:
        s = min
    elif colour.hsl.s > max:
        s = max
    else:
        return colour

    # note: confirmed that colorsys hls is equal to colorgram hsl
    # (except for potential rounding differences, but they're not too important)
    hls = (
        colour.hsl.h / 255,
        colour.hsl.l / 255,
        s / 255
    )
    rgb = tuple(int(x * 255) for x in hls_to_rgb(*hls))
    proportion = colour.proportion
    return colorgram.Color(*rgb, proportion)

def _filter_stand_bg_rings(image: Image.Image) -> Image.Image:
    # ensure RGBA
    image = image.convert('RGBA')

    pixels = image.load()
    for x in range(image.width):
        for y in range(image.height):
            colour = pixels[x, y]
            alpha = colour[3]
            alpha = round(alpha * 2.1 - 150)
            alpha = max(alpha, 0)
            alpha = min(alpha, 255)
            colour = colour[0:3] + (alpha,)
            pixels[x, y] = colour

    return image

def gen_stepup_gacha_banner_image(
        bg_name: str,
        card_image_files: List[str],
        title_text: str,
        description_text: str,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    banner_image = Image.new('RGBA', (960, 320), (0, 0, 0, 0))

    if not bg_name:
        bg_name = DEFAULT_BANNER_BG
    # separate on slash character, used to denote multiple backgrounds
    bg_names = bg_name.split('/')

    bg_bytes = read_file(resource_path, ver, f'image/bg/{bg_names[0]}.png')
    bg_image = _load_bg_image(BytesIO(bg_bytes))
    # if there's multiple backgrounds, paste them over, left-to-right
    for i, bg_name in enumerate(bg_names[1:]):
        split_bytes = read_file(resource_path, ver, f'image/bg/{bg_name}.png')
        split_image = _load_bg_image(BytesIO(split_bytes))
        split_mask = _split_bg_image_mask((bg_image.width, bg_image.height),
                                          i + 1 / len(bg_names), 20)
        bg_image.paste(split_image, mask=split_mask)

    banner_image.paste(
        bg_image,
        box=((banner_image.width - bg_image.width) // 2, BANNER_BG_Y)
    )

    # extract dominant colours (colorgram.py)
    dominant_colours = colorgram.extract(bg_image, 4)
    saturated_dominant_colour = dominant_colours[0]
    for colour in dominant_colours:
        if colour.hsl.s > saturated_dominant_colour.hsl.s:
            saturated_dominant_colour = colour
    # ensure colours is distinct enough by clamping to safe-ish ranges
    saturated_dominant_colour = _clamp_colour_lightness(saturated_dominant_colour, 100, 160)
    saturated_dominant_colour = _clamp_colour_sat(saturated_dominant_colour, 160, 255)

    # load and resize card images
    card_image_bytes = [read_file(resource_path, ver, f) for f in card_image_files]
    card_images = [Image.open(BytesIO(b)) for b in card_image_bytes]
    for i, image in enumerate(card_images):
        image = image.convert('RGBA')
        if len(card_images) <= 2:
            scale_width = int(banner_image.height * 1.35)
        elif len(card_images) == 3:
            scale_width = int(banner_image.height * 1.2)
        else:
            scale_width = banner_image.height
        scale_height = image.height * scale_width // image.width
        image = image.resize((scale_width, scale_height))
        image = _filter_stand_bg_rings(image)
        card_images[i] = image

    cards_image = Image.new('RGBA', (BANNER_BG_SIZE[0], BANNER_BG_SIZE[1] + BANNER_BG_Y),
                            (0, 0, 0, 0))

    # hack to draw index 1 and/or 2 last
    if len(card_images) == 3:
        order = [0, 2, 1]
    elif len(card_images) == 4:
        order = [0, 3, 1, 2]
    else:
        order = list(range(len(card_images)))
    for i in order:
        image = card_images[i]
        if len(card_images) == 1:
            x = (cards_image.width - image.width) // 2
        else:
            x = int((cards_image.width - image.width) * i / (len(card_images) - 1))
        x = cards_image.width - image.width - x  # right to left
        cards_image.alpha_composite(image, (x, 0))
    banner_image.alpha_composite(
        cards_image,
        ((banner_image.width - cards_image.width) // 2, 0)
    )

    # add banner text
    if description_text:
        desc_text = _gen_banner_desc_text_image(description_text)
        desc_text_left = banner_image.width - desc_text.width - 24
        desc_text_upper = banner_image.height - desc_text.height - 16
        banner_image.alpha_composite(desc_text, (desc_text_left, desc_text_upper))

    # add title text
    title_text = _gen_gacha_title_text_image(title_text,
                                             saturated_dominant_colour.rgb + (255,))
    title_text_left = 8
    title_text_upper = 6
    banner_image.alpha_composite(title_text, (title_text_left, title_text_upper))

    return banner_image.convert('RGBA')
