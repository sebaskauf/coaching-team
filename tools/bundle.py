#!/usr/bin/env python3
"""Baut den Ordner app/ aus skills/coach/ (eine Quelle, zwei Wege).

    python3 tools/bundle.py            # app/ neu schreiben
    python3 tools/bundle.py --pruefen  # nur prüfen, ob app/ zum Stand von skills/coach/ passt

Erzeugt:
    app/coaching-team.txt        alle Inhalte in einer Datei fürs Claude-Projekt
    app/projekt-anweisungen.txt  Text für die Projekt-Anweisungen
    app/check-in-sonntag.ics     wöchentlicher Check-in (Sonntag 18:00, Europe/Berlin)

Nur Python-Standardbibliothek, ab Python 3.8.
"""
import argparse
import datetime
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(WURZEL, "skills", "coach")
APP = os.path.join(WURZEL, "app")
VORLAGEN = os.path.join(WURZEL, "tools", "app-vorlagen")

sys.path.insert(0, os.path.join(SKILL, "tools"))
import kalender  # noqa: E402

APP_DATEI = "coaching-team.txt"
ICS_START = datetime.date(2026, 10, 18)  # fester Start, damit die Datei reproduzierbar bleibt

# Reihenfolge der Teile: (Quelle relativ zu skills/coach, Überschrift, Kurzname für Verweise)
TEILE = [
    ("SKILL.md", "Chef (so arbeitet dein Team)", "Chef"),
    ("agenten/analyse.md", "Analyse-Agent", "Analyse-Agent"),
    ("agenten/training.md", "Trainings-Agent", "Trainings-Agent"),
    ("agenten/ernaehrung.md", "Ernährungs-Agent", "Ernährungs-Agent"),
    ("agenten/form.md", "Form-Agent", "Form-Agent"),
    ("agenten/check.md", "Check-Agent", "Check-Agent"),
    ("wissen/training.md", "Wissen Training", "Wissen Training"),
    ("wissen/uebungen.md", "Übungsbibliothek", "Übungsbibliothek"),
    ("wissen/ernaehrung.md", "Wissen Ernährung", "Wissen Ernährung"),
    ("vorlagen/akte.md", "Vorlage Coaching-Akte", "Vorlage Coaching-Akte"),
]


class BundleFehler(RuntimeError):
    """Fehler beim Zusammensetzen, mit deutscher Meldung."""


def lesen(pfad):
    if not os.path.isfile(pfad):
        raise BundleFehler("Datei fehlt: {}".format(os.path.relpath(pfad, WURZEL)))
    with open(pfad, encoding="utf-8") as f:
        return f.read()


def ohne_frontmatter(text):
    if text.startswith("---\n"):
        ende = text.find("\n---\n", 4)
        if ende == -1:
            raise BundleFehler("Frontmatter ohne Abschluss in SKILL.md")
        return text[ende + 5:]
    return text


def verweise_ersetzen(text):
    for nr, (quelle, _, kurz) in enumerate(TEILE, start=1):
        if quelle == "SKILL.md":
            continue
        text = text.replace(quelle, "Teil {} ({})".format(nr, kurz))
    return text.replace("| Datei |", "| Wo es steht |")


def version():
    return lesen(os.path.join(SKILL, ".coaching-team")).strip()


def coaching_team_text():
    titel = [t[1] for t in TEILE]
    doppelt = sorted({t for t in titel if titel.count(t) > 1})
    if doppelt:
        raise BundleFehler("Überschrift doppelt: {}".format(", ".join(doppelt)))
    inhalt = " · ".join("Teil {} {}".format(nr, t[2]) for nr, t in enumerate(TEILE, start=1))
    stuecke = [
        "# Coaching-Team · alles in einer Datei",
        "",
        "**Anweisung an Claude:** Du bist das Coaching-Team der Person in diesem Projekt. Arbeite immer nach dieser "
        "Datei, Teil 1 ist der Chef. Ihre Coaching-Akte ist die Projektdatei „coaching-akte“. Gibt es noch keine Akte "
        "oder schreibt die Person „Start“, übernimmt der Analyse-Agent. Sprich Deutsch, duz die Person und antworte "
        "so kurz, dass man es gut am Handy lesen kann.",
        "",
        "Diese Datei ist dein komplettes Coaching-Team für ein Projekt in der Claude-App: ein Chef und fünf "
        "Agenten mit ihrem Fachwissen. Claude liest sie, du musst sie nicht lesen.",
        "",
        "Version {} · github.com/sebaskauf/coaching-team · Gebaut von Sebastian Kauffmann (SKAILE) · MIT-Lizenz".format(
            version()),
        "",
        "Inhalt: {}".format(inhalt),
    ]
    for nr, (quelle, ueberschrift, _) in enumerate(TEILE, start=1):
        text = lesen(os.path.join(SKILL, quelle))
        if quelle == "SKILL.md":
            text = ohne_frontmatter(text)
            text = re.sub(r"^# Coaching-Team\n+", "", text.lstrip("\n"))
        else:
            text = re.sub(r"^# [^\n]+\n+", "", text.lstrip("\n"), count=1)
        if quelle.startswith("vorlagen/"):
            vorlage = lesen(os.path.join(SKILL, quelle)).strip("\n")
            koerper = ("So sieht die Coaching-Akte aus. Gib sie immer komplett und in genau dieser Form aus."
                       "\n\n```markdown\n{}\n```".format(vorlage))
        else:
            koerper = verweise_ersetzen(text.strip("\n"))
        stuecke += ["", "", "# Teil {}: {}".format(nr, ueberschrift), "", koerper]
    ergebnis = "\n".join(stuecke) + "\n"
    teil_titel = re.findall(r"^# Teil \d+: .+$", ergebnis, flags=re.M)
    if len(teil_titel) != len(TEILE):
        raise BundleFehler("Teil-Überschriften stimmen nicht: {} statt {}".format(len(teil_titel), len(TEILE)))
    return ergebnis


def dateien():
    return {
        APP_DATEI: coaching_team_text(),
        "projekt-anweisungen.txt": lesen(os.path.join(VORLAGEN, "projekt-anweisungen.txt")),
        "check-in-sonntag.ics": kalender.ics("sonntag", "18:00", ICS_START),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Baut app/ aus skills/coach/.")
    parser.add_argument("--pruefen", action="store_true", help="nur prüfen, nichts schreiben")
    args = parser.parse_args(argv)
    try:
        soll = dateien()
    except BundleFehler as fehler:
        print("Abbruch: {}".format(fehler), file=sys.stderr)
        return 1
    if args.pruefen:
        abweichend = []
        for name, inhalt in soll.items():
            pfad = os.path.join(APP, name)
            ist = None
            if os.path.isfile(pfad):
                with open(pfad, encoding="utf-8", newline="") as f:
                    ist = f.read()
            if ist != inhalt:
                abweichend.append(name)
        if abweichend:
            print("app/ ist nicht aktuell: {}. Bitte python3 tools/bundle.py ausführen.".format(
                ", ".join(abweichend)), file=sys.stderr)
            return 1
        print("app/ ist aktuell ({} Dateien).".format(len(soll)))
        return 0
    os.makedirs(APP, exist_ok=True)
    for name, inhalt in soll.items():
        with open(os.path.join(APP, name), "w", encoding="utf-8", newline="") as f:
            f.write(inhalt)
    groesse = len(soll[APP_DATEI].encode("utf-8"))
    print("app/ geschrieben: {} ({} KB), projekt-anweisungen.txt, check-in-sonntag.ics".format(
        APP_DATEI, round(groesse / 1024)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
