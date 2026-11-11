from colorsys import hsv_to_rgb
from io import BytesIO
import math
from zipfile import ZipFile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from util import read_file


APK_PATH = 'apk/game.apk'
ICON_RESOURCE_PATH = 'image/lesson/img_limit{chara_id}_{layer_id}.png'
ICON_LAYERS = ('base', 'lv_text', 'shine1', 'shine2', 'shine3', 'shine4', 'shine5')
ICON_LAYER_TO_ID = {name: i+1 for i, name in enumerate(ICON_LAYERS)}
ROULETTE_ICON_RESOURCE_PATH = 'image/lesson/icon_item_{chara_id}.png'
MINI_ICON_RESOURCE_PATH = 'image/lesson/icon_itemmini_{chara_id}.png'
ITEM_ICON_RESOURCE_PATH = 'image/item/item1_{item_id}.png'
ITEM40_ICON_RESOURCE_PATH = 'image/item/item40_1_{item_id}.png'
ITEM94_ICON_RESOURCE_PATH = 'image/item/item94_1_{item_id}.png'
FOT_COMET_RESOURCE_PATH = 'font/FOT-CometStd-B.otf'

RES_PATH = 'res'
RES_VER = 729

# chara_id: (name, hue1, hue2, flip_dir, sat, val, text_val, gamma, black_clip)
NEW_ICON_CHARAS = {
    # 3: ('月', 0, 45.2, False, 1.0, 1.0, 1.1, 1.0, 0.0),
    10: ('かなで', 275, 55, True, 0.68, 1.0, 1.0, 0.9, 0.0),
    11: ('アルミ', 143, 132, False, 1.2, 0.95, 0.9, 1.6, 0.1),
    12: ('ミント', 160, 175, False, 1.1, 1.0, 0.95, 1.5, 0.0),
    13: ('アモル', 50, 60, False, 0.81, 0.93, 0.9, 1.7, 0.25),
    14: ('クゥエル', 305, 320, False, 0.72, 1.0, 1.0, 1.0, 0.0),
    15: ('ベル', 250, 225, False, 0.72, 1.0, 1.0, 0.8, 0.0)
}

# AKARI_TEXT_COLOUR_RGB = (255, 76, 0)
# AKARI_TEXT_COLOUR_HSV = (17, 255, 255)
VER_TEXT_STROKE_WIDTH = 4
VER_TEXT_GLOW_RADIUS = 8
VER_TEXT_GLOW_WIDTH = 18
VER_TEXT_GLOW_OPACITY = 1.5
VER_TEXT_TOTAL_EFFECT_WIDTH = VER_TEXT_STROKE_WIDTH + VER_TEXT_GLOW_WIDTH

LV_TEXT_FAUX_BOLD_WIDTH = 1.5
LV_TEXT_STROKE_WIDTH = 4
LVL_TEXT_STROKE_BLUR = 4
LV_TEXT_GLOW_RADIUS = 8
LV_TEXT_GLOW_WIDTH = 17
LV_TEXT_GLOW_OPACITY = 1.6
LV_TEXT_TOTAL_EFFECT_WIDTH = LV_TEXT_FAUX_BOLD_WIDTH + LV_TEXT_STROKE_WIDTH + LV_TEXT_GLOW_WIDTH

ITEM94_TEXT_FAUX_BOLD_WIDTH = 1
ITEM94_TEXT_STROKE_WIDTH = 7
ITEM94_TEXT_SHADOW_OFFSET = (7, 6)
ITEM94_TEXT_SHADOW_OPACITY = 0.8
ITEM94_TEXT_TOTAL_EFFECT_WIDTH = ITEM94_TEXT_FAUX_BOLD_WIDTH + ITEM94_TEXT_STROKE_WIDTH + max(ITEM94_TEXT_SHADOW_OFFSET)

ITEM94_IMG_SIZE = (745, 745)
ITEM94_BG_RECT_DIM = (680, 680)
ITEM94_BG_RECT_RADIUS = 126
ITEM94_BG_RECT_STROKE_WIDTH = 26
ITEM94_BG_GLOW_RADIUS = 17

# item1 and item94 are both 90x90 and almost identical -
# item1 just has a smaller square/rectangle for the background
ITEM1_IMG_SIZE = (745, 745)
ITEM1_BG_RECT_DIM = (662, 662)
ITEM1_BG_RECT_RADIUS = 124
ITEM1_BG_RECT_STROKE_WIDTH = 26
ITEM1_BG_GLOW_RADIUS = 17

def read_apk_file(name):
    """Read the bytes content of a file in the game's APK."""
    z = ZipFile(APK_PATH, 'r')
    return z.read(f'assets/{name}')

# note: originally experimented with Akari's roulette icon because its text could be
# cropped off cleanly. thst's not needed anymore, but Akari's is still a good base.
AKARI_ICON_LAYERS = {name: Image.open(BytesIO(read_apk_file(ICON_RESOURCE_PATH.format(chara_id=3, layer_id=i+1))))
                     for i, name in enumerate(ICON_LAYERS)}
AKARI_MINI_ICON = Image.open(BytesIO(read_apk_file(MINI_ICON_RESOURCE_PATH.format(chara_id=3))))
AKARI_ITEM40_ICON = Image.open(BytesIO(read_file(RES_PATH, RES_VER, ITEM40_ICON_RESOURCE_PATH.format(item_id=19))))
AKARI_ITEM94_ICON = Image.open(BytesIO(read_file(RES_PATH, RES_VER, ITEM94_ICON_RESOURCE_PATH.format(item_id=19))))

FOT_COMET_OTF_BYTES = read_apk_file(FOT_COMET_RESOURCE_PATH)
ROULETTE_VER_TEXT_FONT_SMALL = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 64)
ROULETTE_VER_TEXT_FONT_LARGE = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 85)
LV_TEXT_FONT = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 130)
ITEM94_VER_TEXT_FONT_SMALL = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 94)
ITEM94_VER_TEXT_FONT_LARGE = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 123)


def _recolour_akari_icon(icon, hue1, hue2, flip_dir, sat, val, gamma, black_clip):
    #img = Image.eval(icon, lambda x: 255 * (x ** gamma) / (255 ** gamma))
    #img.putalpha(icon.getchannel('A'))
    ch_h, ch_s, ch_v = icon.convert('HSV').split()
    hue1 *= 255.0/360.0
    hue2 *= 255.0/360.0

    # Original image's hue is almost entirely within [0, 32].
    # Shift that up to [111, 143] so outliers are equally above and below,
    # then normalise important region to [0, 1]. Finally, scale to newly desired
    # hues and clip.
    ch_h = ch_h.convert('F')
    width, height = ch_h.size
    pixels_h = ch_h.load()
    for y in range(height):
        for x in range(width):
            h = pixels_h[x, y]
            h = (h + 111) % 255.0  # shift up
            h = (h - 111) / 32 # normalise
            if flip_dir:
                if hue1 > hue2:
                    h = hue1 + h * (hue2-hue1+255)  # scale
                    if h > 255:
                        h -= 255
                else:
                    h = hue1 + h * (hue2-hue1-255)  # scale
                    if h < 0:
                        h += 255
            else:
                h = hue1 + h * (hue2-hue1)  # scale
            pixels_h[x, y] = h
    ch_h = ch_h.convert('L')

    ch_s = Image.eval(ch_s, lambda s: s * sat)
    ch_v = Image.eval(ch_v, lambda v: int((v - 255) / (1-black_clip) + 255))
    ch_v = Image.eval(ch_v, lambda v: 255 * (v ** gamma) / (255 ** gamma))
    ch_v = Image.eval(ch_v, lambda v: v * val)

    img = Image.merge('HSV', (ch_h, ch_s, ch_v)).convert('RGBA')
    img.putalpha(icon.convert('RGBA').getchannel('A'))
    return img

def _text_colours(hue, sat, val):
    colour = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat, val))
    glow_sat = min(sat * 0.75, 0.75)
    ver_glow = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, glow_sat, val))
    white = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat * 0.12, 1.0))
    return colour, ver_glow, white

def _item94_text_colour(hue, sat, val):
    colour = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat, val * 0.8))
    shadow = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat, val * 0.4)) + (int(255 * ITEM94_TEXT_SHADOW_OPACITY),)
    white = (255, 255, 255, 255)
    return colour, shadow, white

def _item94_bg_colours(hue1, hue2, glow_hue, sat, val):
    glow = tuple(round(c * 255) for c in hsv_to_rgb(glow_hue / 360, sat, val * 0.78))
    sat = min(sat * 0.85, 0.75)
    val = max(val * 0.8, 0.8)
    colour1 = tuple(round(c * 255) for c in hsv_to_rgb(hue1 / 360, sat * 1.05, val * 0.88))
    colour2 = tuple(round(c * 255) for c in hsv_to_rgb(hue2 / 360, sat * 0.92, val * 1.1))
    white = (255, 255, 255, 255)
    return colour1, colour2, glow, white

def _roulette_ver_text(name, hue, sat, val):
    colour, glow_colour, white = _text_colours(hue, sat, val)

    ver_text = 'Ver\u200a.'
    ver_bbox = ROULETTE_VER_TEXT_FONT_SMALL.getbbox(ver_text)
    ver_metrics = ROULETTE_VER_TEXT_FONT_SMALL.getmetrics()
    ver_ascent = ver_metrics[0]
    ver_descent = ver_metrics[1]
    name_bbox = ROULETTE_VER_TEXT_FONT_LARGE.getbbox(name)
    name_metrics = ROULETTE_VER_TEXT_FONT_LARGE.getmetrics()
    name_ascent = name_metrics[0]
    name_descent = name_metrics[1]

    text_margin = math.ceil(VER_TEXT_TOTAL_EFFECT_WIDTH)
    ver_pos = (
        text_margin - ver_bbox[0],
        text_margin - ver_bbox[1]
    )
    name_pos = (
        ver_pos[0] + ver_bbox[2] + int(text_margin * 0.25),
        text_margin - name_bbox[1]
    )
    ver_pos = (
        ver_pos[0],
        name_pos[1] + name_bbox[3] - ver_bbox[3] - name_descent + ver_descent + 2  # update to align baselines
    )
    image_size = (
        name_pos[0] + name_bbox[2] + text_margin,
        max(ver_pos[1] + ver_bbox[3], name_pos[1] + name_bbox[3]) + text_margin
    )

    # start by creating strokes for glow
    image = Image.new('RGBA', image_size, glow_colour + (0,))
    d = ImageDraw.Draw(image)
    d.text(
        ver_pos,
        ver_text,
        font=ROULETTE_VER_TEXT_FONT_SMALL,
        fill=glow_colour,
        stroke_fill=glow_colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=ROULETTE_VER_TEXT_FONT_LARGE,
        fill=glow_colour,
        stroke_fill=glow_colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    # blur to make glow
    image = image.filter(ImageFilter.GaussianBlur(radius=VER_TEXT_GLOW_RADIUS))
    alpha = image.getchannel('A')
    alpha = alpha.point(lambda p: int(p * VER_TEXT_GLOW_OPACITY))
    image.putalpha(alpha)
    # now actual strokes
    d = ImageDraw.Draw(image)
    d.text(
        ver_pos,
        ver_text,
        font=ROULETTE_VER_TEXT_FONT_SMALL,
        fill=colour,
        stroke_fill=colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=ROULETTE_VER_TEXT_FONT_LARGE,
        fill=colour,
        stroke_fill=colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    # finally the white text
    d.text(
        ver_pos,
        ver_text,
        font=ROULETTE_VER_TEXT_FONT_SMALL,
        fill=white
    )
    d.text(
        name_pos,
        name,
        font=ROULETTE_VER_TEXT_FONT_LARGE,
        fill=white
    )

    return image

def _item94_bg(hue1, hue2, glow_hue, sat, val):
    colour1, colour2, colour_glow, white = _item94_bg_colours(hue1, hue2, glow_hue, sat, val)

    rect_pos = [ITEM94_IMG_SIZE[i]//2 - ITEM94_BG_RECT_DIM[i]//2 for i in range(2)]

    # generate the background gradient image
    grad = Image.new('RGBA', (1, ITEM94_IMG_SIZE[1]), (0, 0, 0, 0))
    grad_mid_col = tuple(int(colour1[i]*0.05 + colour2[i]*0.05 + 255*0.9) for i in range(3))
    pixels = grad.load()
    for y in range(grad.height):
        if y < rect_pos[1]:
            pixels[0, y] = colour1
        elif y >= rect_pos[1] + ITEM94_BG_RECT_DIM[1]:
            pixels[0, y] = colour2
        else:
            pos = (y - rect_pos[1]) / ITEM94_BG_RECT_DIM[1]
            #col = tuple(int(colour1[i] * (1-pos) + colour2[i] * pos) for i in range(3))
            if pos < 0.5:
                pos_adj = (pos * 2) ** 0.68
                col = tuple(int(colour1[i] * (1-pos_adj) + grad_mid_col[i] * pos_adj) for i in range(3))
            else:
                pos_adj = (pos * 2 - 1) ** (1 / 0.68)
                col = tuple(int(grad_mid_col[i] * (1-pos_adj) + colour2[i] * pos_adj) for i in range(3))
            pixels[0, y] = col
    grad = grad.resize(ITEM94_IMG_SIZE)
    grad_alpha = grad.getchannel('A')
    d = ImageDraw.Draw(grad_alpha)
    d.rectangle([(0, 0), grad_alpha.size], fill = (0))  # clear to 0
    d.rounded_rectangle(
        (rect_pos, [rect_pos[i] + ITEM94_BG_RECT_DIM[i] for i in range(2)]),
        ITEM94_BG_RECT_RADIUS,
        (255)  # fill rect
    )
    grad.putalpha(grad_alpha)

    # now the outline and its glow
    outline = Image.new('RGBA', ITEM94_IMG_SIZE, (colour_glow[0], colour_glow[1], colour_glow[2], 0))
    d = ImageDraw.Draw(outline)
    # start with the glow
    d.rounded_rectangle(
        (
            # note: glow is shifted slightly inwards
            [rect_pos[i] + 1 for i in range(2)],
            [rect_pos[i] + ITEM94_BG_RECT_DIM[i] - 2 for i in range(2)]
        ),
        ITEM94_BG_RECT_RADIUS,
        fill=(colour_glow[0], colour_glow[1], colour_glow[2], 0),
        outline=colour1,
        width=ITEM94_BG_RECT_STROKE_WIDTH
    )
    outline = outline.filter(ImageFilter.GaussianBlur(radius=ITEM94_BG_GLOW_RADIUS))
    d = ImageDraw.Draw(outline)
    # then the outline itself
    d.rounded_rectangle(
        (rect_pos, [rect_pos[i] + ITEM94_BG_RECT_DIM[i] for i in range(2)]),
        ITEM94_BG_RECT_RADIUS,
        fill=None,
        outline=white,
        width=ITEM94_BG_RECT_STROKE_WIDTH
    )

    # composite outline over the gradient
    grad.alpha_composite(outline)
    return grad

# item1 and item94 are both 90x90 and almost identical -
# item1 just has a smaller square/rectangle for the background
def _item1_bg(hue1, hue2, glow_hue, sat, val):
    colour1, colour2, colour_glow, white = _item94_bg_colours(hue1, hue2, glow_hue, sat, val)

    rect_pos = [ITEM1_IMG_SIZE[i]//2 - ITEM1_BG_RECT_DIM[i]//2 for i in range(2)]

    # generate the background gradient image
    grad = Image.new('RGBA', (1, ITEM1_IMG_SIZE[1]), (0, 0, 0, 0))
    grad_mid_col = tuple(int(colour1[i]*0.05 + colour2[i]*0.05 + 255*0.9) for i in range(3))
    pixels = grad.load()
    for y in range(grad.height):
        if y < rect_pos[1]:
            pixels[0, y] = colour1
        elif y >= rect_pos[1] + ITEM1_BG_RECT_DIM[1]:
            pixels[0, y] = colour2
        else:
            pos = (y - rect_pos[1]) / ITEM1_BG_RECT_DIM[1]
            #col = tuple(int(colour1[i] * (1-pos) + colour2[i] * pos) for i in range(3))
            if pos < 0.5:
                pos_adj = (pos * 2) ** 0.68
                col = tuple(int(colour1[i] * (1-pos_adj) + grad_mid_col[i] * pos_adj) for i in range(3))
            else:
                pos_adj = (pos * 2 - 1) ** (1 / 0.68)
                col = tuple(int(grad_mid_col[i] * (1-pos_adj) + colour2[i] * pos_adj) for i in range(3))
            pixels[0, y] = col
    grad = grad.resize(ITEM1_IMG_SIZE)
    grad_alpha = grad.getchannel('A')
    d = ImageDraw.Draw(grad_alpha)
    d.rectangle([(0, 0), grad_alpha.size], fill = (0))  # clear to 0
    d.rounded_rectangle(
        (rect_pos, [rect_pos[i] + ITEM1_BG_RECT_DIM[i] for i in range(2)]),
        ITEM1_BG_RECT_RADIUS,
        (255)  # fill rect
    )
    grad.putalpha(grad_alpha)

    # now the outline and its glow
    outline = Image.new('RGBA', ITEM1_IMG_SIZE, (colour_glow[0], colour_glow[1], colour_glow[2], 0))
    d = ImageDraw.Draw(outline)
    # start with the glow
    d.rounded_rectangle(
        (
            # note: glow is shifted slightly inwards
            [rect_pos[i] + 1 for i in range(2)],
            [rect_pos[i] + ITEM1_BG_RECT_DIM[i] - 2 for i in range(2)]
        ),
        ITEM1_BG_RECT_RADIUS,
        fill=(colour_glow[0], colour_glow[1], colour_glow[2], 0),
        outline=colour1,
        width=ITEM1_BG_RECT_STROKE_WIDTH
    )
    outline = outline.filter(ImageFilter.GaussianBlur(radius=ITEM1_BG_GLOW_RADIUS))
    d = ImageDraw.Draw(outline)
    # then the outline itself
    d.rounded_rectangle(
        (rect_pos, [rect_pos[i] + ITEM1_BG_RECT_DIM[i] for i in range(2)]),
        ITEM1_BG_RECT_RADIUS,
        fill=None,
        outline=white,
        width=ITEM1_BG_RECT_STROKE_WIDTH
    )

    # composite outline over the gradient
    grad.alpha_composite(outline)
    return grad

def _item94_ver_text(name, hue, sat, val):
    colour, shadow, white = _item94_text_colour(hue, sat, val)

    ver_text = 'Ver\u200a.'
    ver_bbox = ITEM94_VER_TEXT_FONT_SMALL.getbbox(ver_text)
    ver_metrics = ITEM94_VER_TEXT_FONT_SMALL.getmetrics()
    ver_ascent = ver_metrics[0]
    ver_descent = ver_metrics[1]
    name_bbox = ITEM94_VER_TEXT_FONT_LARGE.getbbox(name)
    name_metrics = ITEM94_VER_TEXT_FONT_LARGE.getmetrics()
    name_ascent = name_metrics[0]
    name_descent = name_metrics[1]

    text_margin = math.ceil(ITEM94_TEXT_TOTAL_EFFECT_WIDTH)
    ver_pos = (
        text_margin - ver_bbox[0],
        text_margin - ver_bbox[1]
    )
    name_pos = (
        ver_pos[0] + ver_bbox[2] + int(text_margin * 0.25),
        text_margin - name_bbox[1]
    )
    ver_pos = (
        ver_pos[0],
        name_pos[1] + name_bbox[3] - ver_bbox[3] - name_descent + ver_descent + 2  # update to align baselines
    )
    image_size = (
        name_pos[0] + name_bbox[2] + text_margin,
        max(ver_pos[1] + ver_bbox[3], name_pos[1] + name_bbox[3]) + text_margin
    )

    # start by creating shadow
    image = Image.new('RGBA', image_size, (colour[0], colour[1], colour[2], 0))
    d = ImageDraw.Draw(image)
    d.text(
        [ver_pos[i] + ITEM94_TEXT_SHADOW_OFFSET[i] for i in range(2)],
        ver_text,
        font=ITEM94_VER_TEXT_FONT_SMALL,
        fill=shadow,
        stroke_fill=shadow,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH + ITEM94_TEXT_STROKE_WIDTH
    )
    d.text(
        [name_pos[i] + ITEM94_TEXT_SHADOW_OFFSET[i] for i in range(2)],
        name,
        font=ITEM94_VER_TEXT_FONT_LARGE,
        fill=shadow,
        stroke_fill=shadow,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH + ITEM94_TEXT_STROKE_WIDTH
    )
    # then strokes
    d.text(
        ver_pos,
        ver_text,
        font=ITEM94_VER_TEXT_FONT_SMALL,
        fill=colour,
        stroke_fill=colour,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH + ITEM94_TEXT_STROKE_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=ITEM94_VER_TEXT_FONT_LARGE,
        fill=colour,
        stroke_fill=colour,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH + ITEM94_TEXT_STROKE_WIDTH
    )
    # no glow here
    # now the white text
    d.text(
        ver_pos,
        ver_text,
        font=ITEM94_VER_TEXT_FONT_SMALL,
        fill=white,
        stroke_fill=white,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=ITEM94_VER_TEXT_FONT_LARGE,
        fill=white,
        stroke_fill=white,
        stroke_width=ITEM94_TEXT_FAUX_BOLD_WIDTH
    )

    return image

def _lv_text(hue, sat, val):
    colour, _, white = _text_colours(hue, sat, val)

    text = 'Lv.'
    text_bbox = LV_TEXT_FONT.getbbox(text)

    text_margin = math.ceil(LV_TEXT_TOTAL_EFFECT_WIDTH)
    text_pos = (
        text_margin - text_bbox[0],
        text_margin - text_bbox[1]
    )
    image_size = (
        text_pos[0] + text_bbox[2] + text_margin,
        text_pos[1] + text_bbox[3] + text_margin
    )

    # start by creating stroke
    image = Image.new('RGBA', image_size, (colour[0], colour[1], colour[2], 0))
    d = ImageDraw.Draw(image)
    d.text(
        text_pos,
        text,
        font=LV_TEXT_FONT,
        fill=colour,
        stroke_fill=colour,
        stroke_width=LV_TEXT_FAUX_BOLD_WIDTH+LV_TEXT_STROKE_WIDTH
    )
    # copy and blur to make glow
    glow = image.filter(ImageFilter.GaussianBlur(radius=LV_TEXT_GLOW_RADIUS))
    glow_alpha = glow.getchannel('A')
    glow_alpha = glow_alpha.point(lambda p: int(p * LV_TEXT_GLOW_OPACITY))
    glow.putalpha(glow_alpha)
    # blur to make a smoother transition/less obvious stroke
    image = image.filter(ImageFilter.GaussianBlur(radius=LVL_TEXT_STROKE_BLUR))
    d = ImageDraw.Draw(image)
    #composite the glow
    image.alpha_composite(glow)
    # now the white text
    d.text(
        text_pos,
        text,
        font=LV_TEXT_FONT,
        fill=white,
        stroke_fill=white,
        stroke_width=LV_TEXT_FAUX_BOLD_WIDTH
    )

    return image

def _gen_layers(chara_id):
    name, hue1, hue2, flip_dir, sat, val, text_val, gamma, black_clip = NEW_ICON_CHARAS[chara_id]

    if flip_dir:
        if hue1 > hue2:
            text_hue = hue1 + (hue2-hue1+360) * 0.15
            if text_hue > 360:
                text_hue -= 360
        else:
            text_hue = hue1 + (hue2-hue1-360) * 0.15
            if text_hue < 0:
                text_hue += 360
    else:
        text_hue = hue1 + (hue2-hue1) * 0.15

    layers = AKARI_ICON_LAYERS.copy()
    for k in layers.keys():
        layers[k] = _recolour_akari_icon(layers[k], hue1, hue2, flip_dir, sat, val, gamma, black_clip)

    # generate "Ver. {name}" text as additional custom layers
    roulette_ver_text = Image.new('RGBA', (640, 640), (128, 128, 128, 0))
    roulette_ver_text_raw = _roulette_ver_text(name, text_hue, sat, text_val)
    roulette_ver_text_pos = (640 - roulette_ver_text_raw.width - 19,
                             640 - roulette_ver_text_raw.height - 18)
    roulette_ver_text.alpha_composite(roulette_ver_text_raw, roulette_ver_text_pos)
    layers['roulette_ver_text'] = roulette_ver_text

    # also generate "Lv." text, to ensure colour matches "Ver." text
    lv_text = Image.new('RGBA', (640, 640), (128, 128, 128, 0))
    lv_text_raw = _lv_text(text_hue, sat, text_val)
    lv_text_pos = (640//2 - lv_text_raw.width//2 + 2, 640//2 - lv_text_raw.height//2 - 11)
    lv_text.alpha_composite(lv_text_raw, lv_text_pos)
    layers['lv_text'] = lv_text

    # fix cropping error in original shine4 layer by pasting a transparent box over it
    transpbox = Image.new('RGBA', (64, 32), (128, 128, 128, 0))
    layers['shine4'].paste(transpbox, (454, 190))

    # text for use in item94 icon
    item94_ver_text = Image.new('RGBA', ITEM94_IMG_SIZE, (128, 128, 128, 0))
    item94_ver_text_raw = _item94_ver_text(name, text_hue, sat, text_val)
    item94_ver_text_pos = (ITEM94_IMG_SIZE[0]//2 - item94_ver_text_raw.width//2 + 4,
                           ITEM94_IMG_SIZE[1] - item94_ver_text_raw.height - 83)
    item94_ver_text.alpha_composite(item94_ver_text_raw, item94_ver_text_pos)
    layers['item94_ver_text'] = item94_ver_text

    # bg for item94 icon
    layers['item94_bg'] = _item94_bg(hue1, hue2, text_hue, sat, val)

    # bg for item1 icon
    layers['item1_bg'] = _item1_bg(hue1, hue2, text_hue, sat, val)

    return layers

def _roulette_icon(layers):
    img_icon = layers['base'].copy()

    #img_lv = Image.new(layers['lv_text'])
    #lv_alpha = img_lv.getchannel('A')
    #lv_alpha = lv_alpha.point(lambda p: int(p * 0.79))
    #img_lv.putalpha(lv_alpha)
    #img_lv2 = img_lv
    #img_lv = ImageChops.hard_light(img_icon, img_lv)
    #img_lv.putalpha(lv_alpha)
    #img_lv.alpha_composite(img_lv2)
    #img_icon.alpha_composite(img_lv)

    # composite "Lv." text layer
    img_lv = layers['lv_text'].copy()
    lv_alpha = img_lv.getchannel('A')
    img_lv_hl = ImageChops.hard_light(img_icon, img_lv)
    lv_hl_alpha = lv_alpha.point(lambda p: int(p * 0.97))
    img_lv_hl.putalpha(lv_hl_alpha)
    img_icon.alpha_composite(img_lv_hl)
    lv_alpha = lv_alpha.point(lambda p: int(p * 0.33))
    img_lv.putalpha(lv_alpha)
    img_icon.alpha_composite(img_lv)

    # composite "Ver." text layer
    img_icon.alpha_composite(layers['roulette_ver_text'])

    # crop and resize
    img_icon = img_icon.crop((19, 32, 619, 632))
    img_icon = img_icon.resize((180, 180), Image.Resampling.BICUBIC)
    return img_icon

def _mini_icon(chara_id):
    name, hue1, hue2, flip_dir, sat, val, text_val, gamma, black_clip = NEW_ICON_CHARAS[chara_id]
    return _recolour_akari_icon(AKARI_MINI_ICON, hue1, hue2, flip_dir, sat, val, gamma, black_clip)

def _item40_icon(chara_id):
    name, hue1, hue2, flip_dir, sat, val, text_val, gamma, black_clip = NEW_ICON_CHARAS[chara_id]
    return _recolour_akari_icon(AKARI_ITEM40_ICON, hue1, hue2, flip_dir, sat, val, gamma, black_clip)

def _item94_icon(layers):
    img = layers['item94_bg'].copy()
    base = layers['base']

    # composite "Lv." text onto base
    img_lv = layers['lv_text'].copy()
    lv_alpha = img_lv.getchannel('A')
    img_lv_hl = ImageChops.hard_light(base, img_lv)
    lv_hl_alpha = lv_alpha.point(lambda p: int(p * 0.97))
    img_lv_hl.putalpha(lv_hl_alpha)
    base.alpha_composite(img_lv_hl)
    lv_alpha = lv_alpha.point(lambda p: int(p * 0.33))
    img_lv.putalpha(lv_alpha)
    base.alpha_composite(img_lv)

    # composite shine layers onto base
    for layer_name in ('shine1', 'shine2', 'shine3', 'shine4', 'shine5'):
        layer = layers[layer_name]
        base.alpha_composite(layer)

    # composite base and text over bg
    img.alpha_composite(base, (img.width//2 - base.width//2 + 6, img.height//2 - base.height//2 + 10))
    img.alpha_composite(layers['item94_ver_text'])
    # resize to 90x90
    img = img.resize((90, 90), Image.Resampling.BICUBIC)
    return img

def _item1_icon(layers):
    img = layers['item1_bg'].copy()
    base = layers['base']

    # composite "Lv." text onto base
    img_lv = layers['lv_text'].copy()
    lv_alpha = img_lv.getchannel('A')
    img_lv_hl = ImageChops.hard_light(base, img_lv)
    lv_hl_alpha = lv_alpha.point(lambda p: int(p * 0.97))
    img_lv_hl.putalpha(lv_hl_alpha)
    base.alpha_composite(img_lv_hl)
    lv_alpha = lv_alpha.point(lambda p: int(p * 0.33))
    img_lv.putalpha(lv_alpha)
    base.alpha_composite(img_lv)

    # composite shine layers onto base
    for layer_name in ('shine1', 'shine2', 'shine3', 'shine4', 'shine5'):
        layer = layers[layer_name]
        base.alpha_composite(layer)

    # composite base and text over bg
    img.alpha_composite(base, (img.width//2 - base.width//2 + 6, img.height//2 - base.height//2 + 10))
    img.alpha_composite(layers['item94_ver_text'])
    # resize to 90x90
    img = img.resize((90, 90), Image.Resampling.BICUBIC)
    return img
    }


for i, chara_id in enumerate(NEW_ICON_CHARAS.keys()):
    layers = _gen_layers(chara_id)
    for j, name in enumerate(ICON_LAYERS):
        layers[name].save(f'img_limit{chara_id}_{j+1}.png')
    img_roulette = _roulette_icon(layers)
    img_roulette.save(f'icon_item_{chara_id}.png')
    mini_icon = _mini_icon(chara_id)
    mini_icon.save(f'icon_itemmini_{chara_id}.png')
    item40_icon = _item40_icon(chara_id)
    item40_icon.save(f'item40_1_{i+25}.png')
    item94_icon = _item94_icon(layers)
    item94_icon.save(f'item94_1_{i+25}.png')
    item1_icon = _item1_icon(layers)
    item1_icon.save(f'item1_{i+25}.png')
