"""Resume vs job description matcher: your strongest matches and gaps, with evidence.

Usage:
    python -m resume_matcher.main --resume resume.pdf --job job.txt
    python -m resume_matcher.main --resume resume.txt --job job.txt -o match.md
    pbpaste | python -m resume_matcher.main --resume resume.pdf      # job description from stdin
"""
import argparse
import base64
import sys
from pathlib import Path

from common.claude import ask
from resume_matcher.prompt import SYSTEM

MAX_TEXT_CHARS = 40000
MAX_PDF_BYTES = 20 * 1024 * 1024


def resume_block(data: bytes, filename: str) -> dict:
    """Turn a resume file into a content block Claude can read (PDF or plain text)."""
    if filename.lower().endswith(".pdf"):
        if len(data) > MAX_PDF_BYTES:
            raise ValueError("That PDF is too large (over 20 MB).")
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": base64.standard_b64encode(data).decode()},
            "title": "Resume",
        }
    if filename.lower().endswith((".docx", ".doc", ".pages")):
        raise ValueError("Save the resume as PDF or plain text first (File > Export / Save as).")
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("The resume is empty.")
    return {"type": "text", "text": f"<resume>\n{text[:MAX_TEXT_CHARS]}\n</resume>"}


def match_resume(resume: dict, job: str) -> str:
    """Compare a resume block (from resume_block) with a job description. Used by the CLI and the test page."""
    if not job.strip():
        raise ValueError("The job description is empty.")
    content = [resume, {"type": "text", "text": f"<job_description>\n{job.strip()[:MAX_TEXT_CHARS]}\n</job_description>"}]
    return ask(SYSTEM, content, effort="high")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--resume", required=True, help="Your resume as .pdf, .txt or .md.")
    parser.add_argument("--job", help="Job description file. Leave out to paste it (stdin).")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    path = Path(args.resume).expanduser()
    if not path.is_file():
        sys.exit(f"Resume not found: {path}")
    if args.job:
        job = Path(args.job).expanduser().read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("Paste the job description, then press Ctrl-D:", file=sys.stderr)
        job = sys.stdin.read()

    if not job.strip():
        sys.exit("The job description is empty.")
    try:
        block = resume_block(path.read_bytes(), path.name)
        print("Comparing your resume with the job (this can take a minute)...", file=sys.stderr)
        result = match_resume(block, job)
    except ValueError as e:
        sys.exit(str(e))
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
