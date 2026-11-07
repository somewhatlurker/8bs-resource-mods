from colorsys import hsv_to_rgb
from io import BytesIO
import math
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFilter, ImageFont


APK_PATH = 'apk/game.apk'
ROULETTE_ICON_RESOURCE_PATH = 'image/lesson/icon_item_{chara_id}.png'
FOT_COMET_RESOURCE_PATH = 'font/FOT-CometStd-B.otf'

# chara_id: (name, hue1, hue2, flip_dir, sat, luma)
NEW_ICON_CHARAS = {
    10: ('かなで', 275, 55, True, 0.7, 1.1),
    11: ('アルミ', 135, 115, False, 1.0, 0.85),
    12: ('ミント', 160, 175, False, 1.0, 1.0),
    13: ('アモル', 50, 60, False, 0.6, 0.9),
    14: ('クゥエル', 305, 325, False, 0.7, 1.0),
    15: ('ベル', 250, 225, False, 0.7, 1.15)
}

AKARI_TEXT_COLOUR_RGB = (255, 76, 0)
AKARI_TEXT_COLOUR_HSV = (17, 255, 255)
TEXT_STROKE_WIDTH = 2
TEXT_GLOW_RADIUS = 3
TEXT_GLOW_WIDTH = 6
TEXT_GLOW_OPACITY = 0.7
TEXT_TOTAL_EFFECT_WIDTH = TEXT_STROKE_WIDTH + TEXT_GLOW_WIDTH


def read_apk_file(name):
    """Read the bytes content of a file in the game's APK."""
    z = ZipFile(APK_PATH, 'r')
    return z.read(f'assets/{name}')

def akari_roulette_mask_fn(x, y):
    # Whether current pixel is fully above all text
    if y < (180 - 40):
        return 255
    # Whether current pixel is above "Ver." text
    if x < (180 - 36) and y < (180 - 33):
        return 255
    # Whether current pixel is left of "Ver." text along diagonal slice
    #if (x * 1.7 + y) < 324:
    #    return True
    val = (324.5 - (x * 1.7 + y)) * 170
    return max(0, min(val, 255))
    #return False

def akari_roulette_mask_px():
    im = Image.new('L', (180, 180))
    pixels = [akari_roulette_mask_fn(x, y) for y in range(180) for x in range(180)]
    im.putdata(pixels)
    return im


akari_roulette_icon_bytes = read_apk_file(ROULETTE_ICON_RESOURCE_PATH.format(chara_id=3))
akari_roulette_icon = Image.open(BytesIO(akari_roulette_icon_bytes))
akari_roulette_mask = akari_roulette_mask_px()
# akari_roulette_mask.save('icon_item_3_mask.png')

akari_roulette_icon_notext = Image.new('RGBA', (180, 180))
akari_roulette_icon_notext = Image.composite(akari_roulette_icon, akari_roulette_icon_notext, akari_roulette_mask)
# akari_roulette_icon_notext.save('icon_item_3_notext.png')
akari_roulette_icon_notext_hsv = akari_roulette_icon.convert('HSV')

fot_comet_otf_bytes = read_apk_file(FOT_COMET_RESOURCE_PATH)
roulette_ver_text_font_small = ImageFont.truetype(BytesIO(fot_comet_otf_bytes), 18)
roulette_ver_text_font_large = ImageFont.truetype(BytesIO(fot_comet_otf_bytes), 24)


def recolour_akari_icon(icon, hue1, hue2, flip_dir, sat, luma):
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
                h = hue1 + h * (hue2-hue1+255)  # scale
                if h > 255:
                    h -= 255
            else:
                h = hue1 + h * (hue2-hue1)  # scale
            pixels_h[x, y] = h
    ch_h = ch_h.convert('L')

    ch_s = Image.eval(ch_s, lambda s: s * sat)
    ch_v = Image.eval(ch_v, lambda v: v * luma)

    img = Image.merge('HSV', (ch_h, ch_s, ch_v)).convert('RGBA')
    img.putalpha(akari_roulette_icon_notext.getchannel('A'))
    return img

def roulette_ver_text(name, hue, sat, luma):
    colour = tuple(round(c * 255) for c in hsv_to_rgb(hue / 360, sat, luma))
    #colour = (colour[0], colour[1], colour[2], 255)

    ver_text = 'Ver .'
    ver_bbox = roulette_ver_text_font_small.getbbox(ver_text)
    ver_metrics = roulette_ver_text_font_small.getmetrics()
    ver_ascent = ver_metrics[0]
    ver_descent = ver_metrics[1]
    name_bbox = roulette_ver_text_font_large.getbbox(name)
    name_metrics = roulette_ver_text_font_large.getmetrics()
    name_ascent = name_metrics[0]
    name_descent = name_metrics[1]

    text_margin = math.ceil(TEXT_TOTAL_EFFECT_WIDTH)
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
        font=roulette_ver_text_font_small,
        fill=colour,
        stroke_fill=(colour[0], colour[1], colour[2], 191),
        stroke_width=TEXT_STROKE_WIDTH
    )
    d.text(
        name_pos,
        name,
        font=roulette_ver_text_font_large,
        fill=colour,
        stroke_fill=(colour[0], colour[1], colour[2], 191),
        stroke_width=TEXT_STROKE_WIDTH
    )
    d.text(
        ver_pos,
        ver_text,
        font=roulette_ver_text_font_small,
        fill=colour,
        stroke_fill=colour,
        stroke_width=TEXT_STROKE_WIDTH-1
    )
    d.text(
        name_pos,
        name,
        font=roulette_ver_text_font_large,
        fill=colour,
        stroke_fill=colour,
        stroke_width=TEXT_STROKE_WIDTH-1
    )
    # copy and blur to make glow
    glow = image.filter(ImageFilter.GaussianBlur(radius=TEXT_GLOW_RADIUS))
    glow_alpha = glow.getchannel('A')
    glow_alpha = glow_alpha.point(lambda p: int(p * TEXT_GLOW_OPACITY))
    glow.putalpha(glow_alpha)
    image.alpha_composite(glow)
    # now the white text
    d.text(
        ver_pos,
        ver_text,
        font=roulette_ver_text_font_small,
        fill=(255, 255, 255)
    )
    d.text(
        name_pos,
        name,
        font=roulette_ver_text_font_large,
        fill=(255, 255, 255)
    )

    return image

def roulette_icon(name, hue1, hue2, flip_dir, sat, luma):
    img_icon = recolour_akari_icon(akari_roulette_icon_notext, hue1, hue2, flip_dir, sat, luma)
    img_text = roulette_ver_text(name, hue1 + (hue2-hue1)*0.1, sat, luma)
    text_pos = (img_icon.width - img_text.width + 2, img_icon.height - img_text.height - 1)
    img_icon.alpha_composite(img_text, text_pos)
    return img_icon

# recolour_akari_roulette(180, 280).save('icon_item_3_cyanpurp.png')
for chara_id, x in NEW_ICON_CHARAS.items():
    # x is (name, hue1, hue2, flip_dir, sat, luma)
    img = roulette_icon(*x)
    img.save(f'icon_item_{chara_id}.png')
