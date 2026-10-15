import io
import json
import os
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "skills", "coach", "tools"))
import rechner  # noqa: E402


class TestRechner(unittest.TestCase):
    def test_beispiel_aus_wissen_exakt(self):
        e = rechner.bedarf("m", 30, 180, 85, 1.55, "abnehmen")
        self.assertEqual(e["grundumsatz_kcal"], 1830)
        self.assertEqual(e["tagesbedarf_kcal"], 2840)
        self.assertEqual(e["kalorienziel_kcal"], 2270)
        self.assertEqual(e["protein_g"], 155)
        self.assertEqual(e["protein_spanne_g"], [135, 185])
        self.assertEqual(e["fett_min_g"], 70)
        self.assertEqual(e["kohlenhydrate_g"], 260)
        self.assertAlmostEqual(e["roh"]["tagesbedarf"], 2836.5)
        self.assertAlmostEqual(e["roh"]["kalorienziel"], 2269.2)

    def test_wissen_datei_nennt_dieselben_zahlen(self):
        pfad = os.path.join(WURZEL, "skills", "coach", "wissen", "ernaehrung.md")
        with open(pfad, encoding="utf-8") as f:
            text = f.read()
        abschnitt = text.split("## 6.")[1].split("## 7.")[0]
        fett = [int(z.replace(".", "")) for z in re.findall(r"\*\*([\d.]+) (?:kcal|g)\*\*", abschnitt)]
        e = rechner.bedarf("m", 30, 180, 85, 1.55, "abnehmen")
        self.assertEqual(fett, [e["grundumsatz_kcal"], e["tagesbedarf_kcal"], e["kalorienziel_kcal"],
                                e["protein_g"], e["fett_min_g"], e["kohlenhydrate_g"]])

    def test_frau_formel(self):
        e = rechner.bedarf("w", 30, 165, 65, 1.375, "halten")
        # 650 + 1031,25 − 150 − 161 = 1370,25
        self.assertAlmostEqual(e["roh"]["grundumsatz"], 1370.25)
        self.assertEqual(e["grundumsatz_kcal"], 1370)
        self.assertEqual(e["kalorienziel_kcal"], e["tagesbedarf_kcal"])
        self.assertEqual(e["anpassung_prozent"], 0)

    def test_untergrenze_grundumsatz(self):
        e = rechner.bedarf("w", 30, 165, 65, 1.2, "abnehmen", defizit=25)
        self.assertTrue(e["untergrenze_grundumsatz_aktiv"])
        self.assertEqual(e["kalorienziel_kcal"], e["grundumsatz_kcal"])
        self.assertIn("auf den Grundumsatz begrenzt", rechner.lesbar(e))

    def test_keine_untergrenze_wenn_nicht_noetig(self):
        e = rechner.bedarf("m", 30, 180, 85, 1.55, "abnehmen", defizit=25)
        self.assertFalse(e["untergrenze_grundumsatz_aktiv"])
        self.assertGreater(e["kalorienziel_kcal"], e["grundumsatz_kcal"])

    def test_rundung(self):
        self.assertEqual(rechner.runde(2836.5, 10), 2840)
        self.assertEqual(rechner.runde(2835.0, 10), 2840)
        self.assertEqual(rechner.runde(2834.9, 10), 2830)
        self.assertEqual(rechner.runde(153, 5), 155)
        self.assertEqual(rechner.runde(152.4, 5), 150)
        self.assertEqual(rechner.runde(68, 5), 70)

    def test_muskeln_standard_nach_erfahrung(self):
        neu = rechner.bedarf("m", 25, 180, 75, 1.55, "muskeln")
        alt = rechner.bedarf("m", 25, 180, 75, 1.55, "muskeln", erfahrung="fortgeschritten")
        self.assertEqual(neu["anpassung_prozent"], 10)
        self.assertEqual(alt["anpassung_prozent"], 5)
        self.assertGreater(neu["kalorienziel_kcal"], alt["kalorienziel_kcal"])

    def test_protein_bei_bmi_ab_30_auf_zielgewicht(self):
        e = rechner.bedarf("m", 40, 175, 110, 1.375, "abnehmen", zielgewicht=85)
        self.assertGreaterEqual(e["bmi"], 30)
        self.assertEqual(e["bezugsgewicht_kg"], 85)
        self.assertEqual(e["protein_g"], rechner.runde(85 * 1.8, 5))
        ohne = rechner.bedarf("m", 40, 175, 110, 1.375, "abnehmen")
        self.assertAlmostEqual(ohne["bezugsgewicht_kg"], round(25 * 1.75 ** 2, 1))

    def test_wochen_bis_zielgewicht(self):
        e = rechner.bedarf("m", 30, 180, 85, 1.55, "abnehmen", zielgewicht=79)
        self.assertEqual(e["wochen_bis_zielgewicht"], [8, 15])

    def test_ungueltige_eingaben(self):
        with self.assertRaises(rechner.EingabeFehler):
            rechner.bedarf("m", 17, 180, 85, 1.55, "abnehmen")
        with self.assertRaises(rechner.EingabeFehler):
            rechner.bedarf("m", 30, 180, 85, 1.6, "abnehmen")
        with self.assertRaises(rechner.EingabeFehler):
            rechner.bedarf("m", 30, 180, 85, 1.55, "abnehmen", defizit=40)
        with self.assertRaises(rechner.EingabeFehler):
            rechner.bedarf("x", 30, 180, 85, 1.55, "abnehmen")

    def test_kommandozeile(self):
        aus = io.StringIO()
        with redirect_stdout(aus):
            code = rechner.main(["bedarf", "--geschlecht", "m", "--alter", "30", "--groesse", "180",
                                 "--gewicht", "85", "--aktivitaet", "1.55", "--ziel", "abnehmen", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(aus.getvalue())["kalorienziel_kcal"], 2270)
        fehler = io.StringIO()
        with redirect_stderr(fehler), redirect_stdout(io.StringIO()):
            code = rechner.main(["bedarf", "--geschlecht", "m", "--alter", "15", "--groesse", "180",
                                 "--gewicht", "85", "--aktivitaet", "1.55", "--ziel", "abnehmen"])
        self.assertEqual(code, 1)
        self.assertIn("Erwachsene", fehler.getvalue())


if __name__ == "__main__":
    unittest.main()
