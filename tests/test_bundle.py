import os
import re
import sys
import unittest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "tools"))
import bundle  # noqa: E402

AGENTEN = ["Analyse-Agent", "Trainings-Agent", "Ernährungs-Agent", "Form-Agent", "Check-Agent"]


class TestBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dateien = bundle.dateien()
        cls.text = cls.dateien[bundle.APP_DATEI]

    def test_alle_teile_in_reihenfolge(self):
        titel = re.findall(r"^# Teil (\d+): (.+)$", self.text, flags=re.M)
        self.assertEqual([int(n) for n, _ in titel], list(range(1, len(bundle.TEILE) + 1)))
        self.assertEqual([t for _, t in titel], [t[1] for t in bundle.TEILE])

    def test_jede_quelle_steckt_drin(self):
        for quelle, _, _ in bundle.TEILE:
            with open(os.path.join(bundle.SKILL, quelle), encoding="utf-8") as f:
                zeilen = [z for z in f.read().splitlines()
                          if len(z) > 40 and not z.startswith("#") and "/" not in z and "|" not in z]
            for z in zeilen[:5]:
                self.assertIn(z.strip(), self.text, quelle)

    def test_keine_dateipfade_mehr(self):
        self.assertIsNone(re.search(r"\b(agenten|wissen|vorlagen)/\w+\.md", self.text))
        self.assertNotIn("name: coach", self.text)

    def test_agenten_namen_wie_im_video(self):
        titel = re.findall(r"^# Teil \d+: (.+)$", self.text, flags=re.M)
        team = self.text.split("## Dein Team")[1].split("## ")[0]
        for name in AGENTEN:
            self.assertIn(name, titel)
            self.assertIn("| {} |".format(name), team)
        self.assertNotIn("Technik-Agent", self.text)
        self.assertNotIn("Check-in-Agent", self.text)

    def test_akte_vorlage_unveraendert_im_codeblock(self):
        with open(os.path.join(bundle.SKILL, "vorlagen", "akte.md"), encoding="utf-8") as f:
            vorlage = f.read().strip("\n")
        self.assertIn("```markdown\n" + vorlage + "\n```", self.text)

    def test_app_ordner_ist_aktuell(self):
        for name, inhalt in self.dateien.items():
            pfad = os.path.join(bundle.APP, name)
            self.assertTrue(os.path.isfile(pfad), "fehlt: app/" + name)
            with open(pfad, encoding="utf-8", newline="") as f:
                self.assertEqual(f.read(), inhalt, "app/{} ist veraltet: python3 tools/bundle.py".format(name))

    def test_projekt_anweisungen_verweisen_auf_dateien(self):
        anweisungen = self.dateien["projekt-anweisungen.txt"]
        self.assertIn("„coaching-team“", anweisungen)
        self.assertIn("„coaching-akte“", anweisungen)
        self.assertTrue(bundle.APP_DATEI.startswith("coaching-team"))

    def test_groesse_passt_ins_projekt(self):
        self.assertLess(len(self.text.encode("utf-8")), 200 * 1024)

    def test_keine_em_dashes_und_echte_umlaute(self):
        for name, inhalt in self.dateien.items():
            self.assertNotIn("—", inhalt, name)
        self.assertIsNone(re.search(r"\b(fuer|ueber|Uebung|Rueck|koennen|muessen|Groesse)\b", self.text))

    def test_uebungsbibliothek_format(self):
        with open(os.path.join(bundle.SKILL, "wissen", "uebungen.md"), encoding="utf-8") as f:
            text = f.read()
        eintraege = re.split(r"\n(?=## )", text)[1:]
        self.assertGreaterEqual(len(eintraege), 40)
        for e in eintraege:
            zeilen = e.strip().splitlines()
            self.assertEqual(len(zeilen), 6, zeilen[0])
            self.assertTrue(zeilen[1].startswith("Muskeln:"), zeilen[0])
            self.assertTrue(zeilen[2].startswith("Kernpunkte:"), zeilen[0])
            self.assertTrue(zeilen[3].startswith("Häufige Fehler:"), zeilen[0])
            self.assertTrue(zeilen[4].startswith("Bei "), zeilen[0])
            self.assertTrue(zeilen[5].startswith("Leichter / schwerer:"), zeilen[0])

    def test_fehlende_datei_bricht_ab(self):
        alt = bundle.TEILE
        try:
            bundle.TEILE = alt + [("wissen/gibt-es-nicht.md", "Extra", "Extra")]
            with self.assertRaises(bundle.BundleFehler):
                bundle.coaching_team_text()
            bundle.TEILE = alt + [("wissen/training.md", "Wissen Training", "Doppelt")]
            with self.assertRaises(bundle.BundleFehler):
                bundle.coaching_team_text()
        finally:
            bundle.TEILE = alt


if __name__ == "__main__":
    unittest.main()
