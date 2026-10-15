import os
import shutil
import subprocess
import tempfile
import unittest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASH = shutil.which("bash")
GIT = shutil.which("git")


def ist_git_repo():
    if not GIT:
        return False
    r = subprocess.run([GIT, "-C", WURZEL, "rev-parse", "HEAD"], capture_output=True)
    return r.returncode == 0


@unittest.skipUnless(BASH and ist_git_repo() and os.name != "nt", "braucht bash, git und ein geklontes Repo")
class TestInstall(unittest.TestCase):
    def lauf(self, tmp):
        env = dict(os.environ, COACHING_TEAM_REPO_URL=WURZEL, COACHING_TEAM_HOME=os.path.join(tmp, "daten"),
                   CLAUDE_CONFIG_DIR=os.path.join(tmp, "claude"))
        return subprocess.run([BASH, os.path.join(WURZEL, "install.sh")], env=env, capture_output=True, text=True)

    def test_installiert_nur_den_skill_und_aktualisiert(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.lauf(tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            ziel = os.path.join(tmp, "claude", "skills", "coach")
            self.assertTrue(os.path.isfile(os.path.join(ziel, "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(ziel, ".coaching-team")))
            self.assertFalse(os.path.exists(os.path.join(tmp, "claude", "agents")))
            self.assertEqual(sorted(os.listdir(os.path.join(tmp, "claude"))), ["skills"])
            r2 = self.lauf(tmp)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("aktualisiert", r2.stdout)

    def test_fremder_ordner_wird_nicht_ueberschrieben(self):
        with tempfile.TemporaryDirectory() as tmp:
            fremd = os.path.join(tmp, "claude", "skills", "coach")
            os.makedirs(fremd)
            with open(os.path.join(fremd, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write("fremd")
            r = self.lauf(tmp)
            self.assertEqual(r.returncode, 2)
            self.assertIn("Abbruch", r.stderr)
            with open(os.path.join(fremd, "SKILL.md"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "fremd")
            self.assertFalse(os.path.exists(os.path.join(tmp, "daten")))


if __name__ == "__main__":
    unittest.main()
