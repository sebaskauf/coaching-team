#!/usr/bin/env python3
"""Wöchentlicher Check-in als Kalender-Datei (.ics) für das Coaching-Team.

Nur Python-Standardbibliothek, ab Python 3.8. Funktioniert mit Apple Kalender, Google Kalender und Outlook.

Beispiel:
    python3 kalender.py --tag sonntag --uhrzeit 18:00 --ziel check-in.ics
"""
import argparse
import datetime
import re
import sys

TAGE = {
    "montag": ("MO", 0), "dienstag": ("TU", 1), "mittwoch": ("WE", 2), "donnerstag": ("TH", 3),
    "freitag": ("FR", 4), "samstag": ("SA", 5), "sonntag": ("SU", 6),
}
KURZ = {"mo": "montag", "di": "dienstag", "mi": "mittwoch", "do": "donnerstag", "fr": "freitag",
        "sa": "samstag", "so": "sonntag"}
TITEL = "Check-in mit meinem Coaching-Team"
BESCHREIBUNG = "Öffne Claude → Projekt „Mein Coaching-Team“ → schreib: Check-in"
DAUER_MINUTEN = 15

# Europe/Berlin mit Sommerzeit-Regeln (EU seit 1996), damit jeder Kalender die Zeit richtig anzeigt.
VTIMEZONE = [
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Berlin",
    "BEGIN:DAYLIGHT",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "TZNAME:CEST",
    "DTSTART:19700329T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "TZNAME:CET",
    "DTSTART:19701025T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "END:VTIMEZONE",
]


class EingabeFehler(ValueError):
    """Ungültige Eingabe mit deutscher Meldung."""


def tag_normalisieren(tag):
    t = tag.strip().lower().rstrip(".")
    t = KURZ.get(t, t)
    if t not in TAGE:
        raise EingabeFehler("Tag bitte als Montag bis Sonntag angeben (z. B. sonntag).")
    return t


def uhrzeit_lesen(uhrzeit):
    m = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?\s*$", uhrzeit.lower())
    if not m:
        raise EingabeFehler("Uhrzeit bitte als HH:MM angeben (z. B. 18:00).")
    stunde, minute = int(m.group(1)), int(m.group(2) or 0)
    if not (0 <= stunde <= 23 and 0 <= minute <= 59):
        raise EingabeFehler("Uhrzeit bitte als HH:MM zwischen 00:00 und 23:59 angeben.")
    return stunde, minute


def naechster_tag(start, wochentag):
    """Erstes Datum ab start (inklusive), das auf den Wochentag fällt."""
    return start + datetime.timedelta(days=(wochentag - start.weekday()) % 7)


def text_escapen(wert):
    return (wert.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def falten(zeile):
    """Zeilen nach RFC 5545 auf höchstens 75 Bytes falten, ohne UTF-8-Zeichen zu zerschneiden."""
    roh = zeile.encode("utf-8")
    if len(roh) <= 75:
        return [zeile]
    teile, aktuell, grenze = [], b"", 75
    for zeichen in zeile:
        b = zeichen.encode("utf-8")
        if len(aktuell) + len(b) > grenze:
            teile.append(aktuell.decode("utf-8"))
            aktuell, grenze = b"", 74  # Folgezeilen beginnen mit einem Leerzeichen
        aktuell += b
    teile.append(aktuell.decode("utf-8"))
    return [teile[0]] + [" " + t for t in teile[1:]]


def ics(tag="sonntag", uhrzeit="18:00", start=None):
    """Gibt die .ics-Datei als Text (CRLF) zurück. start = Datum, ab dem der erste Termin gesucht wird."""
    t = tag_normalisieren(tag)
    kuerzel, wochentag = TAGE[t]
    stunde, minute = uhrzeit_lesen(uhrzeit)
    start = start or datetime.date.today()
    erster = naechster_tag(start, wochentag)
    beginn = datetime.datetime(erster.year, erster.month, erster.day, stunde, minute)
    ende = beginn + datetime.timedelta(minutes=DAUER_MINUTEN)
    fmt = "%Y%m%dT%H%M%S"
    zeilen = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Coaching-Team//Check-in//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ] + VTIMEZONE + [
        "BEGIN:VEVENT",
        "UID:coaching-team-checkin-{}-{:02d}{:02d}@coaching-team".format(kuerzel.lower(), stunde, minute),
        "DTSTAMP:{}Z".format(datetime.datetime(start.year, start.month, start.day).strftime(fmt)),
        "DTSTART;TZID=Europe/Berlin:{}".format(beginn.strftime(fmt)),
        "DTEND;TZID=Europe/Berlin:{}".format(ende.strftime(fmt)),
        "RRULE:FREQ=WEEKLY;BYDAY={}".format(kuerzel),
        "SUMMARY:{}".format(text_escapen(TITEL)),
        "DESCRIPTION:{}".format(text_escapen(BESCHREIBUNG)),
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:{}".format(text_escapen(TITEL)),
        "TRIGGER:-PT0M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    gefaltet = []
    for z in zeilen:
        gefaltet.extend(falten(z))
    return "\r\n".join(gefaltet) + "\r\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Wöchentlichen Check-in als .ics-Datei erzeugen.")
    parser.add_argument("--tag", default="sonntag", help="Montag bis Sonntag (Standard: sonntag)")
    parser.add_argument("--uhrzeit", default="18:00", help="HH:MM (Standard: 18:00)")
    parser.add_argument("--ziel", default="check-in.ics", help="Dateiname (Standard: check-in.ics)")
    parser.add_argument("--start", help="erstes mögliches Datum JJJJ-MM-TT (Standard: heute)")
    args = parser.parse_args(argv)
    try:
        start = datetime.datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
        inhalt = ics(args.tag, args.uhrzeit, start)
    except EingabeFehler as fehler:
        print("Fehler: {}".format(fehler), file=sys.stderr)
        return 1
    except ValueError:
        print("Fehler: Startdatum bitte als JJJJ-MM-TT angeben.", file=sys.stderr)
        return 1
    with open(args.ziel, "w", encoding="utf-8", newline="") as f:
        f.write(inhalt)
    print("Kalender-Datei gespeichert: {} (jeden {} um {}, 15 Minuten, Erinnerung zur Startzeit).".format(
        args.ziel, tag_normalisieren(args.tag).capitalize(), args.uhrzeit))
    print("Öffnen: Doppelklick (Mac/Windows) oder am Handy antippen und „Zum Kalender hinzufügen“ wählen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
