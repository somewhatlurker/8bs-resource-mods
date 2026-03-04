from colorsys import hls_to_rgb
from io import BytesIO
import math
from typing import List

import colorgram
from PIL import Image, ImageDraw, ImageFont

from util import read_file


DEFAULT_BANNER_BG = 'bg_live_1'

BANNER_FONT_PATH = 'fonts/BIZ_UDPMincho/BIZUDPMincho-Bold.ttf'
BANNER_SMALL_FONT = ImageFont.truetype(BANNER_FONT_PATH, 16)
BANNER_MEDIUM_FONT = ImageFont.truetype(BANNER_FONT_PATH, 24)
BANNER_LARGE_FONT = ImageFont.truetype(BANNER_FONT_PATH, 40)

BANNER_TITLE_GRADIENT_COLOURS = (
    (255, 117, 20, 255), (255, 240, 40, 255), (255, 117, 20, 255)
)
BANNER_TITLE_INNER_STROKE_COLOUR = (255, 240, 200, 255)
BANNER_TITLE_INNER_STROKE_WIDTH = 3.4
BANNER_TITLE_OUTER_STROKE_WIDTH = 2
BANNER_TITLE_TOTAL_STROKE_WIDTH = BANNER_TITLE_INNER_STROKE_WIDTH + BANNER_TITLE_OUTER_STROKE_WIDTH
BANNER_TITLE_INNER_SHADOW_COLOUR = (8, 2, 0, 191)

BANNER_DESCRIPTION_BG_ALPHA = (0, 255, 255, 0)
BANNER_DESCRIPTION_STROKE_WIDTH = 2
BANNER_DESCRIPTION_TEXT_COLOUR = (255, 255, 255, 255)
BANNER_DESCRIPTION_SPACE_QUOTES = True


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

    text_margin = math.ceil(BANNER_TITLE_TOTAL_STROKE_WIDTH)
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
    """Create Image of banner description text with stroke and background."""
    text_margin = math.ceil(BANNER_DESCRIPTION_STROKE_WIDTH)

    if BANNER_DESCRIPTION_SPACE_QUOTES:
        # hacky fix to make some proportional fonts look better
        text = text.replace('「', ' 「').replace('」', '」 ')
        text = text.replace('『', ' 『').replace('』', '』 ')
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
    image_size[1] = font_height + BANNER_DESCRIPTION_STROKE_WIDTH * 2
    for line in lines[1:]:
        # not sure if this is right for line height, but it's close enough
        image_size[1] += font_metrics[0] + BANNER_DESCRIPTION_STROKE_WIDTH * 2
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


def _load_500x120_bg_image(bg_io):
    """Load, crop, and resize bg image to 500x120 resolution RGBA.

    Input is a file-like IO object.
    """
    image = Image.open(bg_io)
    # convert to RGBA because input may be indexed colour
    image = image.convert('RGBA')

    # crop to correct aspect ratio (same as 500x120 image)
    crop_width = image.width
    crop_height = int(image.width * (120 / 500))
    if (crop_height > image.height):
        crop_width = int(image.height * (500 / 120))
        crop_height = image.height
    crop_left = (image.width - crop_width) // 2
    crop_upper = (image.height - crop_height) // 2
    image = image.crop(
        (crop_left, crop_upper, crop_left + crop_width, crop_upper + crop_height)
    )
    # resize to 500x120
    image = image.resize((500, 120))

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


def gen_gacha_banner_image(
        bg_name: str,
        card_image_files: List[str],
        description_text: str,
        resource_path: str,
        ver: int
    ) -> Image.Image:
    if not bg_name:
        bg_name = DEFAULT_BANNER_BG
    # separate on slash character, used to denote multiple backgrounds
    bg_names = bg_name.split('/')

    bg_bytes = read_file(resource_path, ver, f'image/bg/{bg_names[0]}.png')
    banner_image = _load_500x120_bg_image(BytesIO(bg_bytes))

    # if there's multiple backgrounds, paste them over, left-to-right
    for i, bg_name in enumerate(bg_names[1:]):
        split_bytes = read_file(resource_path, ver, f'image/bg/{bg_name}.png')
        split_image = _load_500x120_bg_image(BytesIO(split_bytes))
        split_mask = _split_bg_image_mask((500, 120), i + 1 / len(bg_names), 20)
        banner_image.paste(split_image, mask=split_mask)

    # extract dominant colours (colorgram.py)
    dominant_colours = colorgram.extract(banner_image, 4)
    darkest_dominant_colour = dominant_colours[0]
    lightest_dominant_colour = dominant_colours[0]
    saturated_dominant_colour = dominant_colours[0]
    for colour in dominant_colours:
        if colour.hsl.l < darkest_dominant_colour.hsl.l:
            darkest_dominant_colour = colour
        if colour.hsl.l > lightest_dominant_colour.hsl.l:
            lightest_dominant_colour = colour
        if colour.hsl[1] > saturated_dominant_colour.hsl[1]:
            saturated_dominant_colour = colour
    # ensure colours are distinct enough by fudging values
    if darkest_dominant_colour.hsl.l > 91:
        mult = 91 / darkest_dominant_colour.hsl.l
        rgb = tuple(int(x * mult) for x in darkest_dominant_colour.rgb)
        proportion = darkest_dominant_colour.proportion
        darkest_dominant_colour = colorgram.Color(*rgb, proportion)
    if lightest_dominant_colour.hsl.l < 160:
        mult = 160 / lightest_dominant_colour.hsl.l
        rgb = tuple(int(x * mult) for x in lightest_dominant_colour.rgb)
        proportion = lightest_dominant_colour.proportion
        lightest_dominant_colour = colorgram.Color(*rgb, proportion)
    if saturated_dominant_colour.hsl.l > 191:
        mult = 191 / saturated_dominant_colour.hsl.l
        rgb = tuple(int(x * mult) for x in saturated_dominant_colour.rgb)
        proportion = saturated_dominant_colour.proportion
        saturated_dominant_colour = colorgram.Color(*rgb, proportion)
    if saturated_dominant_colour.hsl.s < 127:
        hls = (
            saturated_dominant_colour.hsl.h / 255,
            saturated_dominant_colour.hsl.l / 255,
            127 / 255
        )
        rgb = tuple(int(x * 255) for x in hls_to_rgb(*hls))
        proportion = saturated_dominant_colour.proportion
        saturated_dominant_colour = colorgram.Color(*rgb, proportion)
    if lightest_dominant_colour.hsl.s > 191:
        # note: confirmed that colorsys hls is equal to colorgram hsl
        # (except for potential rounding differences, but they're not too important)
        hls = (
            lightest_dominant_colour.hsl.h / 255,
            lightest_dominant_colour.hsl.l / 255,
            191 / 255
        )
        rgb = tuple(int(x * 255) for x in hls_to_rgb(*hls))
        proportion = lightest_dominant_colour.proportion
        lightest_dominant_colour = colorgram.Color(*rgb, proportion)
    if saturated_dominant_colour.hsl.s > 191:
        hls = (
            saturated_dominant_colour.hsl.h / 255,
            saturated_dominant_colour.hsl.l / 255,
            191 / 255
        )
        rgb = tuple(int(x * 255) for x in hls_to_rgb(*hls))
        proportion = saturated_dominant_colour.proportion
        saturated_dominant_colour = colorgram.Color(*rgb, proportion)

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
