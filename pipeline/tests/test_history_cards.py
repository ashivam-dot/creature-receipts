from PIL import Image, ImageDraw, ImageStat

from ytc import plates


def test_landscape_archive_photo_remains_visible_below_print():
    # A wide photo has little height on a phone; its backdrop must carry visible scene detail below the print.
    photo = Image.new("RGB", (960, 600), "#dddddd")
    draw = ImageDraw.Draw(photo)
    draw.rectangle((0, 150, 960, 500), fill="#333333")
    for x in range(0, 960, 120):
        draw.rectangle((x, 300, x + 55, 600), fill="#bbbbbb")
    plate = plates.card(photo)
    lower = plate.crop((0, round(plates.PH * 0.67), plates.PW, round(plates.PH * 0.9)))
    gray = ImageStat.Stat(lower.convert("L"))
    assert gray.mean[0] > 80  # not the almost black empty band in the old template
    assert gray.stddev[0] > 35  # source detail is still visible at phone size


def test_tall_archive_print_clears_caption_area():
    # Below the cover threshold, a portrait is framed as a card.
    photo = Image.new("RGB", (700, 1000), "#eeeeee")
    plate = plates.card(photo)
    # The paper border is much brighter than the dark backing. Captions begin near 60% of the final frame.
    assert ImageStat.Stat(plate.crop((80, round(plates.PH * 0.56), plates.PW - 80,
                                     round(plates.PH * 0.59))).convert("L")).mean[0] < 180
