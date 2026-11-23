"""Create a folder of small made-up photos (with camera dates and GPS) to try the organiser on.

    python -m photo_organiser.examples.make_sample_photos ~/Desktop/sample-photos
"""
import sys
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

# (start, count, minutes apart, colour, label, (lat, lon) or None)
EVENTS = [
    (datetime(2026, 7, 14, 10, 5), 6, 25, (70, 160, 220), "Beach", (36.96, -122.02)),
    (datetime(2026, 8, 2, 15, 0), 5, 15, (240, 170, 60), "Birthday", None),
    (datetime(2026, 10, 10, 9, 30), 8, 90, (60, 140, 70), "Hike", (37.74, -119.57)),
    (datetime(2026, 10, 11, 8, 0), 4, 60, (60, 140, 70), "Hike", (37.73, -119.56)),
    (datetime(2026, 11, 3, 18, 45), 1, 0, (120, 120, 120), "Receipt", None),
]


def _dms(value: float) -> tuple:
    value = abs(value)
    d = int(value)
    m = int((value - d) * 60)
    s = round(((value - d) * 60 - m) * 60, 2)
    return (Fraction(d), Fraction(m), Fraction(s).limit_denominator(100))


def make(folder: Path) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for start, count, gap, colour, label, gps in EVENTS:
        for i in range(count):
            taken = start + timedelta(minutes=gap * i)
            img = Image.new("RGB", (640, 480), colour)
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), f"{label} {i + 1}", fill="white")
            if label == "Birthday":
                draw.rectangle((250, 250, 390, 380), fill=(250, 240, 230))  # a cake
                for x in range(270, 380, 25):
                    draw.rectangle((x, 215, x + 6, 250), fill=(230, 60, 60))
            exif = Image.Exif()
            exif[306] = taken.strftime("%Y:%m:%d %H:%M:%S")
            exif.get_ifd(0x8769)[36867] = taken.strftime("%Y:%m:%d %H:%M:%S")
            if gps:
                exif.get_ifd(0x8825).update({1: "N" if gps[0] >= 0 else "S", 2: _dms(gps[0]),
                                             3: "E" if gps[1] >= 0 else "W", 4: _dms(gps[1])})
            n += 1
            img.save(folder / f"IMG_{1000 + n}.jpg", exif=exif)
    return n


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(f"Made {make(Path(sys.argv[1]).expanduser())} sample photos in {sys.argv[1]}")
