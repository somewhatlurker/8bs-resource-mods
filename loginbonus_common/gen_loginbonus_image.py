from colorsys import hls_to_rgb
from io import BytesIO
import math
from typing import List, Tuple

import colorgram
from PIL import Image, ImageDraw, ImageFont

from util import read_file

DEFAULT_BG = 'bg_live_1'

# fills entire image
IMAGE_SIZE = (1386, 852)
# portion that's visible on all screens
IMAGE_SAFE_AREA_SIZE = (1136, 640)
IMAGE_SAFE_AREA_MARGINS = tuple(((IMAGE_SIZE[x] - IMAGE_SAFE_AREA_SIZE[x]) // 2 for x in range(2)))

TITLE_FONT_PATH = 'fonts/IBM_Plex_Sans_JP/IBMPlexSansJP-SemiBold.ttf'
TITLE_FONT = ImageFont.truetype(TITLE_FONT_PATH, 72)
SUBTITLE_FONT = ImageFont.truetype(TITLE_FONT_PATH, 48)

ITEMQTY_FONT_PATH = 'fonts/BIZ_UDPMincho/BIZUDPMincho-Bold.ttf'
ITEMQTY_LARGE_FONT = ImageFont.truetype(ITEMQTY_FONT_PATH, 30)
ITEMQTY_SMALL_FONT = ImageFont.truetype(ITEMQTY_FONT_PATH, 20)

TITLE_INNER_STROKE_COLOUR = (255, 255, 255, 255)
TITLE_INNER_STROKE_WIDTH = 4
TITLE_OUTER_STROKE_WIDTH = 5
TITLE_TOTAL_STROKE_WIDTH = TITLE_INNER_STROKE_WIDTH + TITLE_OUTER_STROKE_WIDTH
TITLE_SHADOW_COLOUR = (31, 31, 31, 63)
TITLE_SHADOW_OFFSET = 6
TITLE_SPACE_QUOTES = False

ITEMQTY_COLOUR = (160, 0, 210, 255)
ITEMQTY_STROKE_COLOUR = (255, 255, 255, 255)
ITEMQTY_STROKE_WIDTH = 3

def _gen_title_text_image(text, text_colour, outline_colour, font=TITLE_FONT) -> Image.Image:
    """Create Image of title text (e.g. "HAPPY\nBIRTHDAY\n_____") with strokes."""
    text_margin = math.ceil(TITLE_TOTAL_STROKE_WIDTH)

    if TITLE_SPACE_QUOTES:
        # hacky fix to make some proportional fonts look better
        text = text.replace('「', ' 「').replace('」', '」 ')
        text = text.replace('『', ' 『').replace('』', '』 ')
    lines = text.split('\n')
    # base metrics for first line
    text_bbox = font.getbbox(lines[0])
    text_pos = (text_margin, text_margin - text_bbox[1])
    image_size = [
        text_pos[0] + text_bbox[2] + text_margin,
        text_pos[1] + text_bbox[3] + text_margin
    ]
    # then adjust height and adjust width if necessary for each subsequent line
    font_metrics = font.getmetrics()
    font_height = font_metrics[0] + font_metrics[1]
    # image_size[1] = font_height + TITLE_TOTAL_STROKE_WIDTH * 2
    line_top = text_pos[1]
    for line in lines[1:]:
        # not sure if this is right for line height, but it's close enough
        line_top += font_metrics[0] + TITLE_TOTAL_STROKE_WIDTH * 2
        line_bbox = font.getbbox(line)
        image_size[1] = line_top + line_bbox[3] + text_margin
        line_size_w = text_pos[0] + line_bbox[2] + text_margin
        if line_size_w > image_size[0]:
            image_size[0] = line_size_w

    # create the image according to the computed size
    image = Image.new('RGBA', image_size, (0, 0, 0, 0))

    # draw the strokes, outer to inner
    d = ImageDraw.Draw(image)
    d.text(
        text_pos,
        text,
        font=font,
        fill=outline_colour,
        stroke_fill=outline_colour,
        stroke_width=TITLE_TOTAL_STROKE_WIDTH,
        spacing=0
    )
    d.text(
        text_pos,
        text,
        font=font,
        fill=TITLE_INNER_STROKE_COLOUR,
        stroke_fill=TITLE_INNER_STROKE_COLOUR,
        stroke_width=TITLE_INNER_STROKE_WIDTH,
        spacing=TITLE_OUTER_STROKE_WIDTH*2
    )

    # and finally the main text
    d.text(
        text_pos,
        text,
        font=font,
        fill=text_colour,
        spacing=TITLE_TOTAL_STROKE_WIDTH*2
    )

    return image

def _gen_subtitle_text_image(text, text_colour, outline_colour) -> Image.Image:
    """Create Image of subtitle text with strokes."""
    return _gen_title_text_image(text, text_colour, outline_colour, SUBTITLE_FONT)

def _gen_itemquantity_text_image(quantity) -> Image.Image:
    """Create Image of item quantity text (e.g. "5個") with stroke."""
    quantity = str(quantity)
    suffix = '個'

    qty_bbox = ITEMQTY_LARGE_FONT.getbbox(quantity)
    qty_metrics = ITEMQTY_LARGE_FONT.getmetrics()
    qty_ascent = qty_metrics[0]
    suffix_bbox = ITEMQTY_SMALL_FONT.getbbox(suffix)
    suffix_metrics = ITEMQTY_SMALL_FONT.getmetrics()
    suffix_ascent = suffix_metrics[0]

    text_margin = math.ceil(ITEMQTY_STROKE_WIDTH)
    qty_pos = (
        text_margin - qty_bbox[0],
        text_margin - qty_bbox[1]
    )
    suffix_pos = (
        qty_pos[0] + qty_bbox[2] + int(text_margin * 0.8),
        qty_pos[1] + qty_ascent - suffix_ascent
    )
    image_size = (
        suffix_pos[0] + suffix_bbox[2] + text_margin,
        max(qty_pos[1] + qty_bbox[3], suffix_pos[1] + suffix_bbox[3]) + text_margin
    )

    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)

    # draw the stroke, then the text
    d.text(
        qty_pos,
        quantity,
        font=ITEMQTY_LARGE_FONT,
        fill=ITEMQTY_STROKE_COLOUR,
        stroke_fill=ITEMQTY_STROKE_COLOUR,
        stroke_width=ITEMQTY_STROKE_WIDTH
    )
    d.text(
        suffix_pos,
        suffix,
        font=ITEMQTY_SMALL_FONT,
        fill=ITEMQTY_STROKE_COLOUR,
        stroke_fill=ITEMQTY_STROKE_COLOUR,
        stroke_width=ITEMQTY_STROKE_WIDTH
    )
    d.text(
        qty_pos,
        quantity,
        font=ITEMQTY_LARGE_FONT,
        fill=ITEMQTY_COLOUR
    )
    d.text(
        suffix_pos,
        suffix,
        font=ITEMQTY_SMALL_FONT,
        fill=ITEMQTY_COLOUR
    )

    return image

def _load_bg_image(bg_io):
    """Load, crop, and resize bg image to IMAGE_SIZE resolution RGBA.

    Input is a file-like IO object.
    """
    image = Image.open(bg_io)
    # convert to RGBA because input may be indexed colour
    image = image.convert('RGBA')

    w = IMAGE_SIZE[0]
    h = IMAGE_SIZE[1]

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

def gen_loginbonus_image(
        bg_name: str,
        card_image_files: List[str],
        reward_image_files: List[str],
        reward_quantities: List[int],
        reward_image_pos: List[Tuple[int, int]] | List[List[int]],
        title_text: str,
        subtitle_text: str,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    loginbonus_image = Image.new('RGBA', IMAGE_SIZE, (0, 0, 0, 0))

    if not bg_name:
        bg_name = DEFAULT_BG
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

    loginbonus_image.paste(
        bg_image,
        box=((loginbonus_image.width - bg_image.width) // 2,
             (loginbonus_image.height - bg_image.height) // 2)
    )

    # extract dominant colours (colorgram.py)
    dominant_colours = colorgram.extract(bg_image, 4)
    saturated_dominant_colour = dominant_colours[0]
    for colour in dominant_colours:
        if colour.hsl.s > saturated_dominant_colour.hsl.s:
            saturated_dominant_colour = colour
    # ensure colours is distinct enough by clamping to safe-ish ranges
    saturated_dominant_colour = _clamp_colour_lightness(saturated_dominant_colour, 50, 125)
    saturated_dominant_colour = _clamp_colour_sat(saturated_dominant_colour, 160, 240)

    # note: top edge should align near top of safe area,
    # while bottom is at bottom of image
    cards_image = Image.new(
        'RGBA',
        (
            IMAGE_SIZE[0],
            int(IMAGE_SIZE[1] - IMAGE_SAFE_AREA_MARGINS[1] * 0.6)
        ),
        (0, 0, 0, 0)
    )

    # load and resize card images
    card_image_bytes = [read_file(resource_path, ver, f) for f in card_image_files]
    card_images = [Image.open(BytesIO(b)) for b in card_image_bytes]
    for i, image in enumerate(card_images):
        image = image.convert('RGBA')
        scale_width = cards_image.height
        if len(card_images) <= 1:
            scale_width = int(scale_width * 1.1)
        elif len(card_images) <= 2:
            scale_width = int(scale_width * 1.0)
        else:
            scale_width = max(int(scale_width * 0.85), scale_width - IMAGE_SAFE_AREA_MARGINS[1] + 1)
        scale_height = image.height * scale_width // image.width
        image = image.resize((scale_width, scale_height))
        image = _filter_stand_bg_rings(image)
        card_images[i] = image

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
            x = int((cards_image.width * 1.04 - image.width) * 0.7)
        elif len(card_images) == 2:
            x = int((cards_image.width * 1.04 - image.width) * (0.15 + i / (len(card_images) - 1) * 0.75))
        else:
            x = int((cards_image.width * 1.04 - image.width) * i / (len(card_images) - 1))
        # x = int(cards_image.width * 1.04) - image.width - x + int(image.width * 0.04)  # right to left
        x = x + int(image.width * 0.04)  # left to right
        cards_image.alpha_composite(image, (x, 0))
    loginbonus_image.alpha_composite(
        cards_image,
        ((loginbonus_image.width - cards_image.width) // 2, (loginbonus_image.height - cards_image.height))
    )

    # add title text
    title_text = _gen_title_text_image(title_text,
                                       saturated_dominant_colour.rgb + (255,),
                                       saturated_dominant_colour.rgb + (255,))
    title_text_left = IMAGE_SAFE_AREA_MARGINS[0] + 16
    # title_text_upper = IMAGE_SAFE_AREA_MARGINS[1] + 16
    title_text_upper = IMAGE_SIZE[1] - IMAGE_SAFE_AREA_MARGINS[1] - 128 - title_text.height
    loginbonus_image.alpha_composite(title_text, (title_text_left, title_text_upper))

    # add subtitle text
    subtitle_text = _gen_subtitle_text_image(subtitle_text,
                                             saturated_dominant_colour.rgb + (255,),
                                             saturated_dominant_colour.rgb + (255,))
    # subtitle_text_left = title_text_left
    subtitle_text_left = title_text_left + title_text.width + 16
    # subtitle_text_upper = title_text_upper + title_text.height + 16
    subtitle_text_upper = title_text_upper + title_text.height - subtitle_text.height
    loginbonus_image.alpha_composite(subtitle_text, (subtitle_text_left, subtitle_text_upper))

    # add reward images
    reward_image_bytes = [read_file(resource_path, ver, f) for f in reward_image_files]
    reward_images = [Image.open(BytesIO(b)) for b in reward_image_bytes]
    for i, image in enumerate(reward_images):
        image = image.convert('RGBA')
        image = image.resize((94, 94))
        pos = reward_image_pos[i]
        # pos is measured from bottom-left of safe area, centred on reward icon I think?
        pos = ((pos[0] + IMAGE_SAFE_AREA_MARGINS[0] - 94 // 2),
               (IMAGE_SIZE[1] - IMAGE_SAFE_AREA_MARGINS[1] - pos[1] - 94 // 2))
        loginbonus_image.alpha_composite(image, pos)
        quantity_image = _gen_itemquantity_text_image(reward_quantities[i])
        quantity_pos = ((pos[0] + 103 - quantity_image.width),
                        (pos[1] + 96 - quantity_image.height))
        loginbonus_image.alpha_composite(quantity_image, quantity_pos)

    return loginbonus_image.convert('RGBA')
