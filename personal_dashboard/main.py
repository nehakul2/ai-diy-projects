"""Self-updating personal dashboard: weather, news on your topics, calendar and to-dos from your other projects.

Usage:
    python -m personal_dashboard.main                        # build once, print it, save dashboard.html
    python -m personal_dashboard.main --open                 # ...and open the page in your browser
    python -m personal_dashboard.main --watch 60             # rebuild every 60 minutes (Ctrl-C to stop)
    python -m personal_dashboard.main --local-only           # only your own data, no API call
    python -m personal_dashboard.main --config my.json       # use another settings file
    python -m personal_dashboard.main --init                 # copy the example settings to edit

Settings live in ~/.ai-diy-projects/dashboard.json (the example is used until you create it).
"""
import argparse
import shutil
import sys
import time
import webbrowser

from personal_dashboard.cards import DEFAULT_CONFIG, data_dir, load_config
from personal_dashboard.dashboard import build, save, to_markdown


def run_once(config: str | None, local_only: bool, refresh: int) -> str:
    cfg = load_config(config)
    if not local_only:
        print("Checking the weather and news (this can take a minute)...", file=sys.stderr)
    data = build(cfg, use_web=not local_only)
    path = save(data, refresh)
    print(to_markdown(data))
    print(f"\nSaved {path}", file=sys.stderr)
    return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", help="Settings file (default ~/.ai-diy-projects/dashboard.json).")
    parser.add_argument("--local-only", action="store_true", help="Skip the web part (no API call).")
    parser.add_argument("--watch", type=int, metavar="MINUTES", help="Keep rebuilding every MINUTES (15 or more).")
    parser.add_argument("--open", action="store_true", help="Open the dashboard page in your browser.")
    parser.add_argument("--init", action="store_true", help="Create your own settings file from the example.")
    args = parser.parse_args()

    if args.init:
        target = data_dir() / "dashboard.json"
        if target.exists():
            sys.exit(f"{target} already exists. Edit it directly.")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DEFAULT_CONFIG, target)
        print(f"Created {target}. Edit your name, location, topics, questions and calendar file there.")
        return
    if args.watch is not None and args.watch < 15:
        sys.exit("Use --watch 15 or more. Each web update makes several searches, so very frequent updates add up.")
    refresh = args.watch or 30
    try:
        path = run_once(args.config, args.local_only, refresh)
        if args.open:
            webbrowser.open(f"file://{path}")
        while args.watch:
            print(f"Next update in {args.watch} minutes (Ctrl-C to stop).", file=sys.stderr)
            time.sleep(args.watch * 60)
            run_once(args.config, args.local_only, refresh)
    except ValueError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
