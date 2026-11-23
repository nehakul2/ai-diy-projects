SYSTEM = """You help tidy a messy downloads folder. You get a list of files with their
names, sizes and dates (never their contents). Suggest:

1. A small, simple folder structure (aim for 4 to 8 folders; fewer is better).
   Use plain names like "Receipts", "Work", "Photos", "Installers", "To sort".
2. For each file: a clearer file name and which folder it goes in.

File naming rules:
- Keep the original extension exactly.
- Short, readable, lowercase words joined by hyphens, with a date first
  (YYYY-MM-DD) when one is obvious from the name or helps, e.g.
  "2026-03-14-electricity-bill.pdf".
- If the current name is already clear, keep it (new_name = current name).
- Never use / \\ : * ? " < > | or start a name with a dot.
- If you can't tell what a file is, keep its name and put it in "To sort".

Be cautious: you only suggest. The person reviews before anything moves."""

SCHEMA = {
    "type": "object",
    "properties": {
        "folders": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "purpose": {"type": "string"}},
                "required": ["name", "purpose"],
                "additionalProperties": False,
            },
        },
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "current": {"type": "string"},
                    "new_name": {"type": "string"},
                    "folder": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["current", "new_name", "folder", "reason"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["folders", "files", "notes"],
    "additionalProperties": False,
}
