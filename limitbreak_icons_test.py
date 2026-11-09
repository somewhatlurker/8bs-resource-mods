from colorsys import hsv_to_rgb
from io import BytesIO
import math
from zipfile import ZipFile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


APK_PATH = 'apk/game.apk'
ICON_RESOURCE_PATH = 'image/lesson/img_limit{chara_id}_{layer_id}.png'
ICON_LAYERS = ('base', 'lv_text', 'shine1', 'shine2', 'shine3', 'shine4', 'shine5')
ICON_LAYER_TO_ID = {name: i+1 for i, name in enumerate(ICON_LAYERS)}
ROULETTE_ICON_RESOURCE_PATH = 'image/lesson/icon_item_{chara_id}.png'
FOT_COMET_RESOURCE_PATH = 'font/FOT-CometStd-B.otf'

# chara_id: (name, hue1, hue2, flip_dir, sat, val, gamma)
NEW_ICON_CHARAS = {
    # 3: ('月', 0, 45.2, False, 1.0, 1.0, 1.0),
    10: ('かなで', 275, 55, True, 0.68, 1.0, 0.9),
    11: ('アルミ', 143, 132, False, 1.3, 0.95, 2.25),
    12: ('ミント', 160, 175, False, 1.2, 1.0, 1.5),
    13: ('アモル', 50, 60, False, 0.81, 0.93, 3.0),
    14: ('クゥエル', 305, 320, False, 0.72, 1.0, 1.0),
    15: ('ベル', 250, 225, False, 0.72, 1.0, 0.8)
}

# AKARI_TEXT_COLOUR_RGB = (255, 76, 0)
# AKARI_TEXT_COLOUR_HSV = (17, 255, 255)
VER_TEXT_STROKE_WIDTH = 4
VER_TEXT_GLOW_RADIUS = 8
VER_TEXT_GLOW_WIDTH = 18
VER_TEXT_GLOW_OPACITY = 0.85
VER_TEXT_TOTAL_EFFECT_WIDTH = VER_TEXT_STROKE_WIDTH + VER_TEXT_GLOW_WIDTH

LV_TEXT_FAUX_BOLD_WIDTH = 1.5
LV_TEXT_STROKE_WIDTH = 2.5
LV_TEXT_GLOW_RADIUS = 7
LV_TEXT_GLOW_WIDTH = 16
LV_TEXT_GLOW_OPACITY = 2.8
LV_TEXT_TOTAL_EFFECT_WIDTH = LV_TEXT_FAUX_BOLD_WIDTH + LV_TEXT_STROKE_WIDTH + LV_TEXT_GLOW_WIDTH

def read_apk_file(name):
    """Read the bytes content of a file in the game's APK."""
    z = ZipFile(APK_PATH, 'r')
    return z.read(f'assets/{name}')

# note: originally experimented with Akari's roulette icon because its text could be
# cropped off cleanly. thst's not needed anymore, but Akari's is still a good base.
AKARI_ICON_LAYERS = {name: Image.open(BytesIO(read_apk_file(ICON_RESOURCE_PATH.format(chara_id=3, layer_id=i+1))))
                     for i, name in enumerate(ICON_LAYERS)}

FOT_COMET_OTF_BYTES = read_apk_file(FOT_COMET_RESOURCE_PATH)
VER_TEXT_FONT_SMALL = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 63)
VER_TEXT_FONT_LARGE = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 85)
LV_TEXT_FONT = ImageFont.truetype(BytesIO(FOT_COMET_OTF_BYTES), 130)


def _recolour_akari_icon(icon, hue1, hue2, flip_dir, sat, val, gamma):
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
    ch_v = Image.eval(ch_v, lambda v: 255 * (v ** gamma) / (255 ** gamma))
    ch_v = Image.eval(ch_v, lambda v: v * val)

    img = Image.merge('HSV', (ch_h, ch_s, ch_v)).convert('RGBA')
    img.putalpha(icon.convert('RGBA').getchannel('A'))
    return img

def _text_colours(hue, sat, val):
    colour = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat, val))
    white = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat * 0.12, 1.0))
    return colour, white

def _ver_text(name, hue, sat, val):
    colour, white = _text_colours(hue, sat, val)

    ver_text = 'Ver .'
    ver_bbox = VER_TEXT_FONT_SMALL.getbbox(ver_text)
    ver_metrics = VER_TEXT_FONT_SMALL.getmetrics()
    ver_ascent = ver_metrics[0]
    ver_descent = ver_metrics[1]
    name_bbox = VER_TEXT_FONT_LARGE.getbbox(name)
    name_metrics = VER_TEXT_FONT_LARGE.getmetrics()
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
        name_pos[1] + name_bbox[3] - ver_bbox[3] - name_descent + ver_descent  # update to align baselines
    )
    image_size = (
        name_pos[0] + name_bbox[2] + text_margin,
        max(ver_pos[1] + ver_bbox[3], name_pos[1] + name_bbox[3]) + text_margin
    )

    # start by creating strokes
    image = Image.new('RGBA', image_size, (colour[0], colour[1], colour[2], 0))
    d = ImageDraw.Draw(image)
    d.text(
        ver_pos,
        ver_text,
        font=VER_TEXT_FONT_SMALL,
        fill=colour,
        stroke_fill=colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=VER_TEXT_FONT_LARGE,
        fill=colour,
        stroke_fill=colour,
        stroke_width=VER_TEXT_STROKE_WIDTH
    )
    # copy and blur to make glow
    glow = image.filter(ImageFilter.GaussianBlur(radius=VER_TEXT_GLOW_RADIUS))
    glow_alpha = glow.getchannel('A')
    glow_alpha = glow_alpha.point(lambda p: int(p * VER_TEXT_GLOW_OPACITY))
    glow.putalpha(glow_alpha)
    image.alpha_composite(glow)
    # now the white text
    d.text(
        ver_pos,
        ver_text,
        font=VER_TEXT_FONT_SMALL,
        fill=white
    )
    d.text(
        name_pos,
        name,
        font=VER_TEXT_FONT_LARGE,
        fill=white
    )

    return image

def _lv_text(hue, sat, val):
    colour, white = _text_colours(hue, sat, val)

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
    name, hue1, hue2, flip_dir, sat, val, gamma = NEW_ICON_CHARAS[chara_id]

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
        layers[k] = _recolour_akari_icon(layers[k], hue1, hue2, flip_dir, sat, val, gamma)

    # generate "Ver. {name}" text as additional custom layer
    ver_text = Image.new('RGBA', (640, 640), (128, 128, 128, 0))
    ver_text_raw = _ver_text(name, text_hue, sat, val)
    ver_text_pos = (640 - ver_text_raw.width - 19, 640 - ver_text_raw.height - 17)
    ver_text.alpha_composite(ver_text_raw, ver_text_pos)
    layers['ver_text'] = ver_text

    # also generate "Lv." text, to ensure colour matches "Ver." text
    lv_text = Image.new('RGBA', (640, 640), (128, 128, 128, 0))
    lv_text_raw = _lv_text(text_hue, sat, val)
    lv_text_pos = (640//2 - lv_text_raw.width//2 + 2, 640//2 - lv_text_raw.height//2 - 11)
    lv_text.alpha_composite(lv_text_raw, lv_text_pos)
    layers['lv_text'] = lv_text

    # fix cropping error in original shine4 layer by pasting a transparent box over it
    transpbox = Image.new('RGBA', (64, 32), (128, 128, 128, 0))
    layers['shine4'].paste(transpbox, (454, 190))

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
    img_lv = layers['lv_text']
    lv_alpha = img_lv.getchannel('A')
    img_lv_hl = ImageChops.hard_light(img_icon, img_lv)
    lv_hl_alpha = lv_alpha.point(lambda p: int(p * 0.97))
    img_lv_hl.putalpha(lv_hl_alpha)
    img_icon.alpha_composite(img_lv_hl)
    lv_alpha = lv_alpha.point(lambda p: int(p * 0.33))
    img_lv.putalpha(lv_alpha)
    img_icon.alpha_composite(img_lv)

    # composite "Ver." text layer
    img_text = layers['ver_text']
    img_icon.alpha_composite(layers['ver_text'])

    # crop and resize
    img_icon = img_icon.crop((19, 32, 619, 632))
    img_icon = img_icon.resize((180, 180), Image.Resampling.BICUBIC)
    return img_icon

# recolour_akari_roulette(180, 280).save('icon_item_3_cyanpurp.png')
for chara_id in NEW_ICON_CHARAS.keys():
    # x is (name, hue1, hue2, flip_dir, sat, val, gamma)
    layers = _gen_layers(chara_id)
    for i, name in enumerate(ICON_LAYERS):
        layers[name].save(f'img_limit{chara_id}_{i+1}.png')
    img_roulette = _roulette_icon(layers)
    img_roulette.save(f'icon_item_{chara_id}.png')
