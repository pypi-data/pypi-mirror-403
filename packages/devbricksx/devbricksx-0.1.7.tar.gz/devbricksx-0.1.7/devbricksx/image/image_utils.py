import PIL
from PIL import Image, ImageDraw
import numpy as np


class Rect:
    left = None
    top = None
    right = None
    bottom = None
    width = None
    height = None
    center = None

    def __init__(self, left, top, right, bottom):
        assert (right > left)
        assert (bottom > top)

        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = (self.right - self.left)
        self.height = (self.bottom - self.top)
        self.center = (self.left + round(self.width / 2),
                       self.top + round(self.height / 2))

    def __str__(self):
        return '(%d , %d) - (%d, %d), [%d, %d], center: (%s)' \
               % (self.left, self.top, self.right, self.bottom,
                  self.width, self.height,
                  self.center)

    def copy(self):
        return Rect(self.left, self.top, self.right, self.bottom)

    def intersect(self, left, top, right, bottom):
        if self.left < right and left < self.right \
                and self.top < bottom and top < self.bottom:
            if self.left < left:
                self.left = left

            if self.top < top:
                self.top = top

            if self.right > right:
                self.right = right

            if self.bottom > bottom:
                self.bottom = bottom

            return True

        return False

    def intersect_with_rect(self, rect):
        return self.intersect(rect.left, rect.top, rect.right, rect.bottom)

    def draw_on_image(self, image, fill=None, outline=None, draw_center=False):
        draw_rect_on_image(image, self.left, self.top, self.right, self.bottom,
                           fill, outline, draw_center)

    def draw_inside_chord_on_image(self, image, start, end, fill=None, outline=None):
        draw_chord_on_image(image, self.left, self.top, self.right, self.bottom,
                            start, end, fill, outline)

    @classmethod
    def from_points(cls, left_top, right_bottom):
        return cls(left_top[0], left_top[1], right_bottom[0], right_bottom[1])


def resize_image(image, dest_width, dest_height):
    owidth, oheight = image.size
    nwidth = dest_width
    nheight = dest_height

    new_image = image.copy()

    if owidth > nwidth:
        if oheight > nheight:
            scale_width = float(nwidth) / owidth
            scale_height = float(nheight) / oheight
            if scale_width > scale_height:
                scaled = scale_image(image, scale_width, owidth, oheight)

                rect = Rect(0, (scaled.size[1] - nheight) / 2,
                            nwidth, nheight)
                new_image = clip_image_with_rect(scaled, rect)
            else:
                scaled = scale_image(image, scale_height, owidth, oheight)

                rect = Rect((scaled.size[0] - nwidth) / 2, 0,
                            nwidth, nheight)
                new_image = clip_image_with_rect(scaled, rect)
        else:
            rect = Rect(owidth - nwidth) / 2, 0, nwidth, nheight
            new_image = clip_image_with_rect(image, rect)
    elif owidth <= nwidth:
        if oheight > nheight:
            rect = Rect(0, (oheight - nheight) / 2, owidth, oheight)
            new_image = clip_image_with_rect(image, rect)
        else:
            new_image = image.resize((nwidth, nheight), PIL.Image.Resampling.LANCZOS)

    return new_image


def scale_image(image, scale, width, height):
    tw = round(width * scale)
    th = round(height * scale)

    return image.resize((int(tw), int(th)), PIL.Image.Resampling.LANCZOS)


def resize_image_lock_ratio(image, dest_width, dest_height):
    dest_min = min(dest_width, dest_height)
    if dest_min < 0:
        return image

    w = image.size[0]
    h = image.size[1]

    if w > h:
        tw = dest_min
        th = (tw * h / w)
    elif w < h:
        th = dest_min
        tw = (th * w / h)
    else:
        tw = th = dest_min

    return image.resize((int(tw), int(th)), PIL.Image.Resampling.LANCZOS)


def clip_image_with_rect(image, rect):
    return image.crop((rect.left, rect.top, rect.right, rect.bottom))


def draw_rect_on_image(image, left, top, right, bottom, fill=None, outline=None, draw_center=False):
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.rectangle([(left, top), (right, bottom)], fill, outline)

    if draw_center:
        center_x = round((left + right) / 2)
        center_y = round((top + bottom) / 2)
        draw.line((center_x, top, center_x, bottom), fill=outline)
        draw.line((left, center_y, right, center_y), fill=outline)

    del draw


def draw_round_rect_on_image(image, left, top, right, bottom, corner_radius, fill=None, outline=None):
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.rectangle(
        [
            (left, top + corner_radius),
            (right, bottom - corner_radius)
        ],
        fill=fill,
        outline=outline
    )
    draw.rectangle(
        [
            (left + corner_radius, top),
            (right - corner_radius, bottom)
        ],
        fill=fill,
        outline=outline
    )
    draw.pieslice(
        [(left, top), (left + corner_radius * 2, top + corner_radius * 2)],
        180,
        270,
        fill=fill,
        outline=outline
        )
    draw.pieslice(
        [(right - corner_radius * 2, bottom - corner_radius * 2), (right, bottom)],
        0,
        90,
        fill=fill,
        outline=outline
        )
    draw.pieslice([(left, bottom - corner_radius * 2),
                   (left + corner_radius * 2, bottom)],
                  90,
                  180,
                  fill=fill,
                  outline=outline
                  )
    draw.pieslice([(right - corner_radius * 2, top),
                   (right, top + corner_radius * 2)],
                  270,
                  360,
                  fill=fill,
                  outline=outline
                  )


def draw_chord_on_image(image, left, top, right, bottom, start, end, fill=None, outline=None):
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.chord([(left, top), (right, bottom)], start, end, fill, outline)
    del draw


def draw_text_on_image(image, left, top, text, font=None, fill=None):
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.text((left, top), text, fill, font)
    del draw


def calculate_brightness(image, pixel_spacing=1):
    pixels = list(image.getdata())

    r = 0
    g = 0
    b = 0
    n = 0

    for p in pixels[::pixel_spacing]:
        # print(p)

        r += p[0]
        g += p[1]
        b += p[2]

        n += 1

    return (r + b + g) / (n * 3)


def clip_image_with_alpha_mask(image, alpha_mask):
    assert (image.size[0] == alpha_mask.size[0] and
            image.size[1] == alpha_mask.size[1])

    image_array = np.asarray(image.convert('RGBA'))
    mask_array = np.asarray(alpha_mask.convert('L'))

    new_array = np.empty(image_array.shape, dtype='uint8')

    # colors (three first columns, RGB)
    new_array[:, :, :3] = image_array[:, :, :3]

    # transparency (4th column)
    new_array[:, :, 3] = mask_array

    return Image.fromarray(new_array)


def image_to_flat_array(image):
    array = np.asarray(image).astype(np.int64)

    return array.reshape((array.shape[0] * array.shape[1], array.shape[2]))


def image_with_mask(image_file, mask_file):
    image = Image.open(image_file)
    mask = Image.open(mask_file)

    if image is None or mask is None:
        return None

    if image.size[0] != mask.size[0] or image.size[1] != mask.size[1]:
        print('dimension of image and mask are not matched.')
        return None

    width = image.size[0]
    height = image.size[1]

    composed = Image.new('RGBA', (width, height))

    composed.paste(image, (0, 0), mask)

    return composed


def detach_alpha_channel(image):
    if image is None:
        return image

    np_image = np.array(image)
    new_image = np.zeros((np_image.shape[0], np_image.shape[1], 3))

    for each_channel in range(3):
        new_image[:, :, each_channel] = np_image[:, :, each_channel]
        # only copy first 3 channels.

    return new_image
