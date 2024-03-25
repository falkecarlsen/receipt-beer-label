from escpos import *
from PIL import Image, ImageDraw, ImageFont
import tabulate

# beer info, at most 6 fields. First is header with beer name
data = {
    "Name": "Test Beer",
    "Style": "IPA",
    "ABV": "5.5%",
    "Batch": "1",
    "Date": "2022-01-01",
    "Description": "A test beer for testing purposes."
}

out_file = "label.bmp"

# printer model name SRP-350 VER.1.24 2003.02.28
# measured width of the paper 78, which is 3 inches
# testing seems to indicate that an image width of 512 is the maximum
p = printer.Serial(devfile='/dev/ttyUSB0',
                   baudrate=19200,
                   bytesize=8,
                   parity='N',
                   stopbits=1,
                   timeout=1.00,
                   dsrdtr=True,
                   )


def generate_label(table, image, out):
    """
    Generate a homebrewed beer label to be printed.
    Style is an ascii table. Due to aspect ratio wishes, image is 1000x512 and in landscape.
    This requires the table to be generated and rotated to a bitmap before being printed.
    Height (which is width) should be respected to retain font size.
    """
    w = 512
    h = 700

    # create image
    img = Image.new('1', (h, w), color=1)
    d = ImageDraw.Draw(img)

    # draw image centered based on width of image
    img.paste(image, ((h - image.width) // 2, 0))

    fnt = ImageFont.truetype('/usr/share/fonts/liberation/LiberationMono-Regular.ttf', 20)

    # draw table below image
    d.text((0, image.height + 10), table, font=fnt, fill=0)

    # rotate
    img = img.rotate(90, expand=True)

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

    p.image(image_path)
    p.cut()


if __name__ == '__main__':
    for i in range(1):
        print_label(data, out_file)