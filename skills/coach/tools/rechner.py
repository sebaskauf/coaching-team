#!/usr/bin/env python3
"""Kalorien- und Proteinbedarf für das Coaching-Team (nur Python-Standardbibliothek, ab Python 3.8).

Beispiel:
    python3 rechner.py bedarf --geschlecht m --alter 30 --groesse 180 --gewicht 85 --aktivitaet 1.55 --ziel abnehmen

Rechenweg wie in wissen/ernaehrung.md: Mifflin-St Jeor, Aktivitätsfaktor, Ziel-Anpassung,
Untergrenze Grundumsatz, Protein 1,6–2,2 g/kg (Standard 1,8), Fett mindestens 0,8 g/kg, Rest Kohlenhydrate.
Gerundet wird erst am Ende: kcal auf 10, Gramm auf 5.
"""
import argparse
import json
import math
import sys

FAKTOREN = (1.2, 1.375, 1.55, 1.725)
ZIELE = ("abnehmen", "halten", "muskeln")


class EingabeFehler(ValueError):
    """Ungültige Eingabe mit deutscher Meldung."""


def runde(wert, schritt):
    """Kaufmännisch runden auf ein Vielfaches von schritt (0,5 rundet auf)."""
    return int(math.floor(wert / schritt + 0.5) * schritt)


def grundumsatz(geschlecht, alter, groesse, gewicht):
    basis = 10 * gewicht + 6.25 * groesse - 5 * alter
    return basis + 5 if geschlecht == "m" else basis - 161


def pruefe(geschlecht, alter, groesse, gewicht, aktivitaet, ziel, zielgewicht, defizit, ueberschuss):
    if geschlecht not in ("m", "w"):
        raise EingabeFehler("Geschlecht bitte als m oder w angeben (nur für die Formel).")
    if not 18 <= alter <= 100:
        raise EingabeFehler("Die Formeln gelten für Erwachsene. Alter bitte zwischen 18 und 100 angeben.")
    if not 120 <= groesse <= 230:
        raise EingabeFehler("Größe bitte in cm angeben (120 bis 230).")
    if not 30 <= gewicht <= 350:
        raise EingabeFehler("Gewicht bitte in kg angeben (30 bis 350).")
    if not any(abs(aktivitaet - f) < 1e-9 for f in FAKTOREN):
        raise EingabeFehler("Aktivitätsfaktor bitte 1.2, 1.375, 1.55 oder 1.725.")
    if ziel not in ZIELE:
        raise EingabeFehler("Ziel bitte abnehmen, halten oder muskeln.")
    if zielgewicht is not None and not 30 <= zielgewicht <= 350:
        raise EingabeFehler("Zielgewicht bitte in kg angeben (30 bis 350).")
    if defizit is not None and not 15 <= defizit <= 25:
        raise EingabeFehler("Defizit bitte zwischen 15 und 25 Prozent.")
    if ueberschuss is not None and not 5 <= ueberschuss <= 10:
        raise EingabeFehler("Überschuss bitte zwischen 5 und 10 Prozent.")


def bedarf(geschlecht, alter, groesse, gewicht, aktivitaet, ziel, zielgewicht=None,
           erfahrung="neu", defizit=None, ueberschuss=None):
    """Gibt ein Dictionary mit allen Zahlen zurück (gerundet) plus Rohwerten."""
    pruefe(geschlecht, alter, groesse, gewicht, aktivitaet, ziel, zielgewicht, defizit, ueberschuss)

    gu = grundumsatz(geschlecht, alter, groesse, gewicht)
    tagesbedarf = gu * aktivitaet

    if ziel == "abnehmen":
        prozent = -(defizit if defizit is not None else 20)
    elif ziel == "muskeln":
        prozent = ueberschuss if ueberschuss is not None else (10 if erfahrung == "neu" else 5)
    else:
        prozent = 0
    kalorienziel = tagesbedarf * (1 + prozent / 100.0)
    untergrenze_aktiv = kalorienziel < gu
    if untergrenze_aktiv:
        kalorienziel = gu

    bmi = gewicht / (groesse / 100.0) ** 2
    if bmi >= 30:
        if zielgewicht is not None:
            bezug, bezug_grund = zielgewicht, "Zielgewicht (BMI ab 30)"
        else:
            bezug, bezug_grund = 25 * (groesse / 100.0) ** 2, "Gewicht bei BMI 25 (BMI ab 30, kein Zielgewicht)"
    else:
        bezug, bezug_grund = gewicht, "aktuelles Gewicht"

    protein = bezug * 1.8
    fett_min = bezug * 0.8
    kohlenhydrate = max(0.0, (kalorienziel - protein * 4 - fett_min * 9) / 4)

    ergebnis = {
        "grundumsatz_kcal": runde(gu, 10),
        "tagesbedarf_kcal": runde(tagesbedarf, 10),
        "kalorienziel_kcal": runde(kalorienziel, 10),
        "ziel": ziel,
        "anpassung_prozent": prozent,
        "untergrenze_grundumsatz_aktiv": untergrenze_aktiv,
        "protein_g": runde(protein, 5),
        "protein_spanne_g": [runde(bezug * 1.6, 5), runde(bezug * 2.2, 5)],
        "fett_min_g": runde(fett_min, 5),
        "kohlenhydrate_g": runde(kohlenhydrate, 5),
        "bezugsgewicht_kg": round(bezug, 1),
        "bezugsgewicht_grund": bezug_grund,
        "bmi": round(bmi, 1),
        "roh": {
            "grundumsatz": round(gu, 2),
            "tagesbedarf": round(tagesbedarf, 2),
            "kalorienziel": round(kalorienziel, 2),
            "protein": round(protein, 2),
            "fett_min": round(fett_min, 2),
            "kohlenhydrate": round(kohlenhydrate, 2),
        },
    }

    if ziel == "abnehmen" and zielgewicht is not None and zielgewicht < gewicht:
        differenz = gewicht - zielgewicht
        ergebnis["wochen_bis_zielgewicht"] = [
            int(math.ceil(differenz / (0.01 * gewicht))),
            int(math.ceil(differenz / (0.005 * gewicht))),
        ]
    return ergebnis


def tausender(zahl):
    return "{:,}".format(zahl).replace(",", ".")


def vorzeichen(prozent):
    betrag = abs(prozent)
    text = str(int(betrag)) if betrag == int(betrag) else str(betrag).replace(".", ",")
    if prozent > 0:
        return "+" + text
    if prozent < 0:
        return "−" + text
    return "±0"


def lesbar(e):
    zeilen = [
        "Grundumsatz: {} kcal".format(tausender(e["grundumsatz_kcal"])),
        "Tagesbedarf: {} kcal".format(tausender(e["tagesbedarf_kcal"])),
        "Kalorienziel: {} kcal ({})".format(
            tausender(e["kalorienziel_kcal"]),
            "auf den Grundumsatz begrenzt" if e["untergrenze_grundumsatz_aktiv"]
            else vorzeichen(e["anpassung_prozent"]) + " %"),
        "Protein: {} g (Spanne {}–{} g)".format(e["protein_g"], *e["protein_spanne_g"]),
        "Fett mindestens: {} g".format(e["fett_min_g"]),
        "Kohlenhydrate (Rest): {} g".format(e["kohlenhydrate_g"]),
    ]
    if e["untergrenze_grundumsatz_aktiv"]:
        zeilen.append("Hinweis: Rechnung lag unter dem Grundumsatz, Kalorienziel auf den Grundumsatz gesetzt.")
    if e["bezugsgewicht_grund"] != "aktuelles Gewicht":
        zeilen.append("Protein und Fett bezogen auf {} kg ({}).".format(
            str(e["bezugsgewicht_kg"]).replace(".", ","), e["bezugsgewicht_grund"]))
    if "wochen_bis_zielgewicht" in e:
        zeilen.append("Zeitraum bis zum Zielgewicht: etwa {}–{} Wochen (0,5–1 % pro Woche).".format(
            *e["wochen_bis_zielgewicht"]))
    return "\n".join(zeilen)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kalorien- und Proteinbedarf für das Coaching-Team.")
    unter = parser.add_subparsers(dest="befehl")
    b = unter.add_parser("bedarf", help="Bedarf, Kalorienziel und Makros berechnen")
    b.add_argument("--geschlecht", required=True, choices=["m", "w"])
    b.add_argument("--alter", required=True, type=int)
    b.add_argument("--groesse", required=True, type=float, help="in cm")
    b.add_argument("--gewicht", required=True, type=float, help="in kg")
    b.add_argument("--aktivitaet", required=True, type=float, help="1.2, 1.375, 1.55 oder 1.725")
    b.add_argument("--ziel", required=True, choices=list(ZIELE))
    b.add_argument("--zielgewicht", type=float)
    b.add_argument("--erfahrung", choices=["neu", "fortgeschritten"], default="neu",
                   help="neu = bis 1 Jahr Training (nur für Ziel muskeln)")
    b.add_argument("--defizit", type=float, help="Prozent, 15 bis 25 (Standard 20)")
    b.add_argument("--ueberschuss", type=float, help="Prozent, 5 bis 10")
    b.add_argument("--json", action="store_true", help="nur JSON ausgeben")
    args = parser.parse_args(argv)
    if args.befehl != "bedarf":
        parser.print_help()
        return 2
    try:
        e = bedarf(args.geschlecht, args.alter, args.groesse, args.gewicht, args.aktivitaet, args.ziel,
                   zielgewicht=args.zielgewicht, erfahrung=args.erfahrung,
                   defizit=args.defizit, ueberschuss=args.ueberschuss)
    except EingabeFehler as fehler:
        print("Fehler: {}".format(fehler), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(e, ensure_ascii=False, indent=2))
    else:
        print(lesbar(e))
        print()
        print(json.dumps(e, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
