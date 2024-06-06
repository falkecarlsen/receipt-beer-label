from escpos import *
from PIL import Image, ImageDraw, ImageFont
import tabulate

test = True

data = {
    "Name": "Captain Haddock's",
    "Style": "Belgian Dubbel IPA",
    "ABV": "8.4%",
    "OG/FG": "1.070 / 1.006",
    "Bottle date": "2024-05-29",
    "Notes": "Guaranteed swearwords!!!"
}
art = "haddock-100-103-crop.png"

out_file = "label.bmp"

# label dimensions
w = 800
h = 512
name_h = 45

h_logo = h - name_h
pad = 5
e = 2

# printer model name SRP-350 VER.1.24 2003.02.28
# measured width of the paper 78, which is 3 inches
# testing seems to indicate that an image width of 512 is the maximum
if not test:
    p = printer.Serial(devfile='/dev/ttyUSB0',
                       baudrate=19200,
                       bytesize=8,
                       parity='N',
                       stopbits=1,
                       timeout=1.00,
                       dsrdtr=True,
                       )


def draw_text_in_box(image, text, box, font_path="arial.ttf"):
    # Unpack the bounding box
    left, top, right, bottom = box
    box_width = right - left
    box_height = bottom - top

    # Initialize drawing context
    draw = ImageDraw.Draw(image)

    # Start with a small font size and increase until the text fits the bounding box
    font_size = 1
    font = ImageFont.truetype(font_path, font_size)

    while True:
        # Measure text size with the current font
        _, _, text_width, text_height = draw.textbbox((0, 0), text=text, font=font)

        # Break if the text fits the bounding box
        if text_width > box_width or text_height > box_height:
            break

        # Increment the font size
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)

    # Use the last font size that fit within the bounding box
    font_size -= 1
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text position to center it within the bounding box
    _, _, text_width, text_height = draw.textbbox((0, 0), text=text, font=font)
    text_x = left + (box_width - text_width) // 2
    text_y = top + (box_height - text_height) // 2

    # Draw the text
    draw.text((text_x, text_y), text, font=font, fill="black", stroke_width=0)

    return image


def apply_art(image: Image, art_path, bbox) -> Image:
    # draw image centered based on width of image
    left, top, right, bot = bbox
    art = Image.open(art_path)
    ratio = min(left - right / art.width, (bot - top) / art.height)
    l_w, l_h = int(art.width * ratio), int(art.height * ratio)
    art = art.resize((l_w - 4 * e, l_h))
    art_start_coord = int((right - left - l_w) / 2)
    return image.paste(art, (left, top))


def apply_data_table(image, table, font, bbox):
    # draw table below image
    left, top, right, bot = bbox
    i_table = Image.new('L', (h, right), color="white")
    d_table = ImageDraw.Draw(i_table)
    d_table.text((0, 0), table, font=font, fill=0)
    i_table = i_table.rotate(-90, expand=True)
    return image.paste(i_table, (0, 0, right, bot))


def generate_label(table, art_path, out):
    """
    Generate a homebrewed beer label to be printed.
    Style is an ascii table. Due to aspect ratio wishes, image is 1000x512 and in landscape.
    This requires the table to be generated and rotated to a bitmap before being printed.
    Height (which is width) should be respected to retain font size.
    """
    font_path = "/usr/share/fonts/liberation/LiberationMono-Regular.ttf"
    font_bold = "/usr/share/fonts/liberation/LiberationSans-BoldItalic.ttf"
    font = ImageFont.truetype(font_path, 20)

    div = 8
    div_space = 2
    b0 = w * 0
    b1 = int(w * div_space / div)
    b2 = int(w * (div - div_space) / div)
    b3 = int(w * div / div)

    # create label
    label = Image.new('1', (w, h), color=1)
    # create draw object
    d = ImageDraw.Draw(label)

    apply_data_table(label, table, font, (0, 0, b1, h))

    apply_art(label, art_path, (b1, pad + e, b2, h_logo))

    draw_text_in_box(label, data['Name'], (b1 + e, h_logo, b2, h - e), font_bold)

    # draw bounding rectangle
    d.rectangle([(0, 0), (b1, h)], outline="black")
    d.rectangle([(b1, 0), (b2, h)], outline="black")
    d.rectangle([(b2, 0), (w, h)], outline="black")

    # save image
    label.save(f"{out}")


def print_label(table_data: dict, image_path: str):
    # get first of dict
    key, value = next(iter(table_data.items()))

    # strip first of dict
    info = dict(list(table_data.items())[1:])

    gen_table = tabulate.tabulate(info.items(),
                                  headers=[key, value],
                                  numalign="left",
                                  stralign="left",
                                  tablefmt='fancy_outline')

    generate_label(gen_table, art, image_path)

    im = Image.open(image_path)
    if test:
        im.show()
    else:
        print("Sending to printer")
        im = im.rotate(90, expand=True)
        im.save(image_path)
        p.image(image_path)
        p.cut()


if __name__ == '__main__':
    for i in range(1):
        print_label(data, out_file)
