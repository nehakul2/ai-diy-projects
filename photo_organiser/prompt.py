NAME_SYSTEM = """You name groups of photos so someone can find them later, like
"Beach day in Santa Cruz" or "Maya's 5th birthday party". Each group is one event:
photos taken close together in time. For each you get the dates, the number of photos,
a rough GPS location if the camera saved one, a few file names, and a few small
thumbnails.

For each event give:
- name: 2 to 6 words, specific but not over-confident. Use what you can see (a
  birthday cake, snow, a wedding, a hike) and the location (name the town or park
  from the GPS when you're confident). Don't name people unless their name is
  written in the photo. Without thumbnails or GPS, use what the dates suggest
  (e.g. "Christmas Day", "Weekend away") or "Photos".
- place: the likely town, park or landmark, or empty if unknown.
- confident: false if the name is mostly a guess.
No dates in the name; they're added automatically."""

NAME_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "name": {"type": "string"},
                    "place": {"type": "string"},
                    "confident": {"type": "boolean"},
                },
                "required": ["number", "name", "place", "confident"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["events"],
    "additionalProperties": False,
}
