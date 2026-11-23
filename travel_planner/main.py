"""Travel planner that checks the boring bits: visas, luggage, check-in and transfers.

Usage:
    python -m travel_planner.main --trip "London to Tokyo via Doha, 3-17 March, then Seoul" \\
        --passport "Indian" --airline "Qatar Airways, economy"
    python -m travel_planner.main --file my_bookings.txt --passport "US"
    python -m travel_planner.main          # asks you each question
"""
import argparse
import sys
from pathlib import Path

from common.claude import WEB_SEARCH, ask
from travel_planner.prompt import SYSTEM

MAX_BOOKING_CHARS = 20000


def plan_trip(trip: str = "", passport: str = "", airline: str = "", notes: str = "", bookings: str = "") -> str:
    """Check a trip and return the Markdown report. Used by the CLI (and any UI)."""
    if not (trip.strip() or bookings.strip()):
        raise ValueError("Need the trip route and dates, or your bookings.")
    details = []
    if trip.strip():
        details.append(f"Trip: {trip.strip()}")
    details.append(f"Passport: {passport.strip() or 'not given'}")
    if airline.strip():
        details.append(f"Airline/fare: {airline.strip()}")
    if notes.strip():
        details.append(f"Notes: {notes.strip()}")
    if bookings.strip():
        details.append(f"<bookings>\n{bookings[:MAX_BOOKING_CHARS]}\n</bookings>")
    return ask(SYSTEM, "\n".join(details), effort="high", tools=[WEB_SEARCH])


def prompt_for(label: str) -> str:
    try:
        return input(f"{label}: ").strip()
    except EOFError:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trip", default="", help="Route and dates, e.g. 'NYC to Lisbon 2-9 May, then Porto'.")
    parser.add_argument("--file", help="A text file with your itinerary or pasted booking emails.")
    parser.add_argument("--passport", default="", help="Passport nationality (entry rules depend on it).")
    parser.add_argument("--airline", default="", help="Airline(s) and fare class, if known.")
    parser.add_argument("--notes", default="", help="Anything else: kids, a pet, a long layover, etc.")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    bookings = Path(args.file).read_text(encoding="utf-8") if args.file else ""
    trip, passport, airline = args.trip, args.passport, args.airline
    interactive = not (trip or bookings)
    if interactive:
        trip = prompt_for("Trip (route and dates)")
        airline = airline or prompt_for("Airline and fare class (optional)")
    if not passport:
        passport = prompt_for("Passport nationality")

    if not (trip.strip() or bookings.strip()):
        sys.exit("Need the trip route and dates, or a file with your bookings.")
    print("Checking visas, luggage and transfers (this can take a minute or two)...", file=sys.stderr)
    try:
        result = plan_trip(trip, passport, airline, args.notes, bookings)
    except ValueError as e:
        sys.exit(str(e))
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
