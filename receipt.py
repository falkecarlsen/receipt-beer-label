from escpos import *
from PIL import Image, ImageDraw, ImageFont, ImageOps
import tabulate

test = True

# beer info, at most 6 fields. First is header with beer name
data = {
    "Name": "Test Beer",
    "Style": "IPAAAA",
    "ABV": "5.5%",
    "Batch": "1",
    "Date": "2022-01-01",
    "Description": "A test beer for testing purposes."
}

out_file = "label.bmp"

# printer model name SRP-350 VER.1.24 2003.02.28
# measured width of the paper 78, which is 3 inches
# testing seems to indicate that an image width of 512 is the maximum
if not test:
    p = printer.Serial(devfile='/dev/ttyUSB0',
                       baudrate=9600,
                       bytesize=8,
                       parity='N',
                       stopbits=1,
                       timeout=1.00,
                       dsrdtr=True,
                       )

from PIL import Image, ImageDraw, ImageFont


def draw_rotated_text_in_place(image, text, bounding_box, font_path=None, font_size=20):
    """
    Draws 90 degrees rotated text within a bounding box on an already loaded image.

    :param image: PIL Image object to modify.
    :param text: The text to be drawn.
    :param bounding_box: Tuple (x, y, width, height) defining the bounding box.
    :param font_path: Path to the .ttf font file to use. Defaults to a basic PIL font.
    :param font_size: Size of the font.
    """
    draw = ImageDraw.Draw(image)

    # Set the font
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    # Create a new image for the rotated text
    _, _, text_height, text_width = font.getbbox(text)
    rotated_image = Image.new('RGBA', (text_height, text_width), (255, 255, 255, 0))
    rotated_draw = ImageDraw.Draw(rotated_image)

    # Draw the text on the new image
    rotated_draw.text((0, 0), text, font=font, fill="black")

    # Rotate the image with the text
    rotated_image = rotated_image.rotate(90, expand=1)

    # Compute the position to paste the rotated text image within the bounding box
    x, y, box_width, box_height = bounding_box
    text_x = x + (box_width - rotated_image.width) // 2
    text_y = y + (box_height - rotated_image.height) // 2

    # Paste the rotated text image onto the original image
    image.paste(rotated_image, (text_x, text_y), rotated_image)

def generate_label(table, image, out):
    """
    Generate a homebrewed beer label to be printed.
    Style is an ascii table. Due to aspect ratio wishes, image is 1000x512 and in landscape.
    This requires the table to be generated and rotated to a bitmap before being printed.
    Height (which is width) should be respected to retain font size.
    """
    fnt = ImageFont.truetype('/usr/share/fonts/liberation/LiberationMono-Regular.ttf', 20)

    w = 800
    h = 512
    pad = 5
    e = 2

    div = 8
    div_space = 2
    b0 = w * 0
    b1 = int(w * div_space / div)
    b2 = int(w * (div - div_space) / div)
    b3 = int(w * div / div)

    # create image
    img = Image.new('1', (w, h), color=1)
    d = ImageDraw.Draw(img)

    # draw first data rectangle
    d.rectangle([(pad, pad), (b1, h - pad)], outline="black")
    d.rectangle([(b1, pad), (b2, h - pad)], outline="black")
    d.rectangle([(b2, pad), (w - pad, h - pad)], outline="black")

    # draw_rotated_text(img, 90, (b1 + e, b2 - e, h - pad - e), "test "*5, "black")

    # draw image centered based on width of image
    #img.paste(image, ((h - image.width) // 2, 0))

    # draw table below image
    i_table = Image.new('L', (b1, h), color="white")

    d_table = ImageDraw.Draw(i_table)
    d_table.text((0, image.height + 10), table, font=fnt, fill=0)
    img.paste(i_table, (0, 0, b1, h), )

    # rotate
    #img = img.rotate(90, expand=True)

    # save image
    img.save(f"{out}")


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

    generate_label(gen_table, Image.open("logo.png"), image_path)

    if test:
        im = Image.open(image_path)
        im = im.rotate(-90, expand=True)
        im.show()
    else:
        print("Sending to printer")
        p.image(image_path)
        p.cut()


if __name__ == '__main__':
    for i in range(1):
        print_label(data, out_file)
