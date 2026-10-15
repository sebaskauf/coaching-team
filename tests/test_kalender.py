import datetime
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
import io

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "skills", "coach", "tools"))
import kalender  # noqa: E402


def entfalten(text):
    """RFC 5545: Zeilen, die mit Leerzeichen beginnen, gehören zur vorherigen."""
    return text.replace("\r\n ", "").split("\r\n")


def feld(zeilen, name):
    return [z.split(":", 1)[1] for z in zeilen if z.split(":", 1)[0].split(";")[0] == name]


class TestKalender(unittest.TestCase):
    def setUp(self):
        self.text = kalender.ics("sonntag", "18:00", datetime.date(2026, 10, 15))
        self.zeilen = entfalten(self.text)

    def test_gueltiges_grundgeruest(self):
        self.assertTrue(self.text.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"))
        self.assertTrue(self.text.endswith("END:VCALENDAR\r\n"))
        for block in ("VCALENDAR", "VTIMEZONE", "VEVENT", "VALARM", "DAYLIGHT", "STANDARD"):
            self.assertEqual(self.zeilen.count("BEGIN:" + block), 1, block)
            self.assertEqual(self.zeilen.count("END:" + block), 1, block)
        self.assertEqual(len(feld(self.zeilen, "PRODID")), 1)
        start, ende = self.zeilen.index("BEGIN:VEVENT"), self.zeilen.index("END:VEVENT")
        termin = self.zeilen[start:ende]
        for pflicht in ("UID", "DTSTAMP", "DTSTART", "DTEND", "SUMMARY", "RRULE"):
            self.assertEqual(len(feld(termin, pflicht)), 1, pflicht)

    def test_nur_crlf_und_kurze_zeilen(self):
        self.assertNotIn("\n", self.text.replace("\r\n", ""))
        for zeile in self.text.split("\r\n"):
            self.assertLessEqual(len(zeile.encode("utf-8")), 75, zeile)

    def test_woechentlich_sonntag_18_uhr_berlin(self):
        self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=SU", self.zeilen)
        self.assertIn("DTSTART;TZID=Europe/Berlin:20261018T180000", self.zeilen)
        self.assertIn("DTEND;TZID=Europe/Berlin:20261018T181500", self.zeilen)
        self.assertIn("TZID:Europe/Berlin", self.zeilen)
        self.assertEqual(datetime.date(2026, 10, 18).weekday(), 6)

    def test_titel_beschreibung_und_umlaute(self):
        self.assertEqual(feld(self.zeilen, "SUMMARY"), ["Check-in mit meinem Coaching-Team"])
        self.assertEqual(feld(self.zeilen, "DESCRIPTION")[0], kalender.BESCHREIBUNG)
        roh = self.text.encode("utf-8")
        self.assertIn("Öffne".encode("utf-8"), roh)
        self.assertIn(b"\xc3\x96ffne", roh)
        self.assertIn("„Mein Coaching-Team“".encode("utf-8"), roh)

    def test_erinnerung_zur_startzeit(self):
        self.assertIn("TRIGGER:-PT0M", self.zeilen)
        self.assertIn("ACTION:DISPLAY", self.zeilen)

    def test_anderer_tag_und_kurzform(self):
        z = entfalten(kalender.ics("Mi", "7:30", datetime.date(2026, 10, 15)))
        self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=WE", z)
        self.assertIn("DTSTART;TZID=Europe/Berlin:20261021T073000", z)

    def test_start_am_selben_tag(self):
        z = entfalten(kalender.ics("donnerstag", "19:00", datetime.date(2026, 10, 15)))
        self.assertIn("DTSTART;TZID=Europe/Berlin:20261015T190000", z)

    def test_escaping(self):
        self.assertEqual(kalender.text_escapen("a,b;c\\d\ne"), "a\\,b\\;c\\\\d\\ne")

    def test_ungueltige_eingaben(self):
        with self.assertRaises(kalender.EingabeFehler):
            kalender.ics("Feiertag", "18:00")
        with self.assertRaises(kalender.EingabeFehler):
            kalender.ics("sonntag", "25:00")

    def test_kommandozeile_schreibt_datei(self):
        with tempfile.TemporaryDirectory() as tmp:
            ziel = os.path.join(tmp, "x.ics")
            with redirect_stdout(io.StringIO()):
                code = kalender.main(["--tag", "sonntag", "--uhrzeit", "18:00", "--ziel", ziel, "--start", "2026-10-15"])
            self.assertEqual(code, 0)
            with open(ziel, "rb") as f:
                self.assertEqual(f.read(), self.text.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
