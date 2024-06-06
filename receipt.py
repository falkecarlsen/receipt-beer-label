from escpos import *
from PIL import Image, ImageDraw, ImageFont
import tabulate
from SimpleFaceGen.face_gen import FaceGen

test = True

data = {
    "Name": "Captain Haddock's",
    "Style": "Belgian Dubbel IPA",
    "ABV": "8.4%",
    "OG/FG": "1.070 / 1.006",
    "Bottle date": "2024-05-29",
    "Notes": "Guaranteed swearwords!!!"
}

contents = {
    "Base": "2-Row, 6.5kg",
    "Spec.": "Special B, 0.5kg",
    "Add.": "Dextrose, 0.5kg",
    "Bitter": "Fuggles, 60g",
    "Mid": "East Kent Goldings, 50g",
    "Aroma": "Styrian Goldings, 45g"
}

batch = 6
bottle = 0
batch_size = 75

art = "haddock-100-103-crop.png"

out_file = "label.bmp"

# label dimensions
w = 800
h = 512

h_name = 45
h_art = h - h_name
h_lot = 25
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


def apply_text(image, text, box, font_path="arial.ttf"):
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

    apply_art(label, art_path, (b1, pad + e, b2, h_art))

    apply_text(label, data['Name'], (b1 + e, h_art, b2, h - e), font_bold)

    col_3 = (b3 - b2)

    # apply face
    face: Image = FaceGen().generate()
    face = face.resize((col_3, col_3))
    label.paste(face, (b2, h - col_3))

    # apply bottle/batch
    apply_text(label, f"no. {bottle}/{batch_size}", (b2, h - h_lot, b3, h - pad), font_path)

    # apply ingredients
    d.text((b2,0), " ".join(f'{k}: {v}' for k, v in contents.items()))

    # draw bounding rectangle
    d.rectangle([(0, 0), (b1, h)], outline="black")
    d.rectangle([(b1, 0), (b2, h)], outline="black")
    d.rectangle([(b2, 0), (w, h)], outline="black")
    d.rectangle([(b2, h - col_3), (b3, h)], outline="black")

    # save image
    label.save(f"{out}")
    return label


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

    label = generate_label(gen_table, art, image_path)

    if test:
        label.show()
    else:
        print("Sending to printer")
        label = label.rotate(90, expand=True)
        label.save(image_path)
        p.image(image_path)
        p.cut()


if __name__ == '__main__':
    for i in range(1):
        print_label(data, out_file)
