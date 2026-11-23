# Photo organiser by event

Turn a folder full of `IMG_4821.jpg` files into folders like:

```
2026-07-14 Beach day in Santa Cruz/
2026-08-02 Birthday party/
2026-10-10 to 11 Yosemite hike/
2026-11 Other photos/
```

How it works:

1. Reads when each photo was taken from the camera data (EXIF), or from the
   file name (`IMG_20260714_103000.jpg`, `Screenshot 2026-07-14 at ...`), or
   finally the file date.
2. Groups photos into **events**: a gap of more than 6 hours starts a new one,
   except photos taken in the same place within a day stay together, so a
   weekend trip isn't split overnight.
3. Claude names each event from the dates, the rough GPS location, and
   **3 small thumbnails**. Groups of fewer than 3 photos go into a monthly
   "Other photos" folder.
4. You see a **preview**. Nothing moves until you say yes, and every run
   writes an undo log.

## Try it

From the repo root, make a folder of sample photos first:

```bash
python -m photo_organiser.examples.make_sample_photos ~/Desktop/sample-photos
python -m photo_organiser.main ~/Desktop/sample-photos               # preview only
python -m photo_organiser.main ~/Desktop/sample-photos --apply       # preview, then ask before moving
python -m photo_organiser.main --undo ~/Desktop/sample-photos/.organiser-undo-<time>.json
```

Options: `--gap 12` (hours that start a new event), `--min-photos 5`,
`--no-thumbnails` (name events from dates and location only), and `--no-ai`
(date-only folder names, no API call).

## Safety and privacy

- Only files directly inside the folder are touched; subfolders and hidden files are skipped.
- Files keep their names. Nothing is deleted or overwritten, and clashes are skipped.
- Sent to Claude: dates, counts, a few file names, GPS rounded to about 1 km, and
  (unless you turn it off) 3 small 384-pixel thumbnails per event. Never the full photos.
- Try it on a copy of a few photos first.

iPhone HEIC photos are sorted using their file name or date, but aren't used as
thumbnails unless you install `pillow-heif`. Videos are sorted by date too.

## Ideas to improve it

- Write the event name into each photo's metadata as well.
- Pick the best photo from each event as a cover.
