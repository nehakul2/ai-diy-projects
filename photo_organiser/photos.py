"""Find when (and roughly where) photos were taken, and group them into events.

Uses Pillow (installed with Streamlit) to read EXIF data. Falls back to dates in file
names (IMG_20260714_103000.jpg, PXL_..., Screenshot 2026-07-14 at ...) and then to the
file's modified time.
"""
import base64
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".tif", ".tiff", ".dng"}
VIDEO_TYPES = {".mov", ".mp4", ".m4v", ".avi", ".3gp"}
NAME_DATE = re.compile(r"(20\d{2}|19\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?:[ _T-]*(?:at )?(\d{2})[.:_-]?(\d{2})[.:_-]?(\d{2}))?")


@dataclass
class Photo:
    path: Path
    taken: datetime
    source: str  # "camera", "file name" or "file date"
    gps: tuple[float, float] | None = None


@dataclass
class Event:
    number: int
    photos: list[Photo] = field(default_factory=list)
    name: str = ""
    place: str = ""
    confident: bool = True

    @property
    def start(self) -> datetime:
        return self.photos[0].taken

    @property
    def end(self) -> datetime:
        return self.photos[-1].taken

    def dates(self) -> str:
        s, e = self.start, self.end
        if s.date() == e.date():
            return f"{s:%Y-%m-%d}"
        if (s.year, s.month) == (e.year, e.month):
            return f"{s:%Y-%m-%d} to {e:%d}"
        return f"{s:%Y-%m-%d} to {e:%Y-%m-%d}"

    def location(self) -> tuple[float, float] | None:
        points = [p.gps for p in self.photos if p.gps]
        if not points:
            return None
        return (round(sum(p[0] for p in points) / len(points), 2), round(sum(p[1] for p in points) / len(points), 2))


def _exif(path: Path) -> tuple[datetime | None, tuple[float, float] | None]:
    try:
        from PIL import Image
        with Image.open(path) as img:
            exif = img.getexif()
    except Exception:  # not an image Pillow can read (e.g. HEIC without a plugin), or no EXIF
        return None, None
    taken = None
    raw = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal, else DateTime
    if raw:
        try:
            taken = datetime.strptime(str(raw).strip()[:19], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass
    gps = None
    g = exif.get_ifd(0x8825)
    try:
        if g and 2 in g and 4 in g:
            to_deg = lambda v: float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600  # noqa: E731
            lat, lon = to_deg(g[2]), to_deg(g[4])
            if g.get(1) == "S":
                lat = -lat
            if g.get(3) == "W":
                lon = -lon
            if lat or lon:
                gps = (lat, lon)
    except (TypeError, ValueError, ZeroDivisionError, IndexError):
        pass
    return taken, gps


def _from_name(name: str) -> datetime | None:
    m = NAME_DATE.search(name)
    if not m:
        return None
    y, mo, d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    try:
        return datetime(y, mo, d, h, mi, s)
    except ValueError:
        return None


def read_photo(path: Path) -> Photo:
    taken, gps = _exif(path) if path.suffix.lower() in PHOTO_TYPES else (None, None)
    if taken:
        return Photo(path, taken, "camera", gps)
    from_name = _from_name(path.stem)
    if from_name and 1990 < from_name.year <= datetime.now().year:
        return Photo(path, from_name, "file name", gps)
    return Photo(path, datetime.fromtimestamp(path.stat().st_mtime), "file date", gps)


def scan(folder: Path, include_videos: bool = True, limit: int = 2000) -> list[Photo]:
    """Photos (and videos) directly inside `folder`, oldest first. Subfolders and hidden files are skipped."""
    if not folder.is_dir():
        raise ValueError(f"Not a folder: {folder}")
    types = PHOTO_TYPES | (VIDEO_TYPES if include_videos else set())
    files = [p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in types]
    if not files:
        raise ValueError(f"No photos found directly inside {folder}.")
    if len(files) > limit:
        raise ValueError(f"{len(files)} photos is more than the limit of {limit}. Try a smaller folder first.")
    return sorted((read_photo(p) for p in files), key=lambda p: (p.taken, p.path.name))


def _near(a: tuple[float, float] | None, b: tuple[float, float] | None, km: float = 15) -> bool:
    return bool(a and b) and abs(a[0] - b[0]) * 111 < km and abs(a[1] - b[1]) * 111 * 0.7 < km


def group_events(photos: list[Photo], gap_hours: float = 6) -> list[Event]:
    """Start a new event whenever there's a gap of more than `gap_hours` between photos.

    Exception: photos taken within a day of each other in the same place (by GPS) stay
    together, so an overnight trip isn't split at night.
    """
    events: list[Event] = []
    for p in photos:
        gap = p.taken - events[-1].end if events else None
        same_trip = gap is not None and gap <= timedelta(hours=24) and _near(p.gps, events[-1].location())
        if gap is None or (gap > timedelta(hours=gap_hours) and not same_trip):
            events.append(Event(len(events) + 1))
        events[-1].photos.append(p)
    return events


def thumbnail_b64(path: Path, size: int = 384) -> str | None:
    """A small JPEG of the photo, base64-encoded, or None if it can't be opened."""
    try:
        from PIL import Image, ImageOps
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((size, size))
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=70)
    except Exception:
        return None
    return base64.b64encode(buf.getvalue()).decode()


def samples(event: Event, k: int = 3) -> list[Path]:
    """Up to k photos spread across the event (Pillow-readable types only)."""
    pics = [p.path for p in event.photos if p.path.suffix.lower() in PHOTO_TYPES - {".heic", ".heif", ".dng"}]
    if len(pics) <= k:
        return pics
    return [pics[round(i * (len(pics) - 1) / (k - 1))] for i in range(k)]
