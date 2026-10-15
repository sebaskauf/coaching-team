#!/usr/bin/env bash
# Coaching-Team: Kopier-Installation für Claude Code (Mac, Linux, Git Bash unter Windows).
# Erster Lauf installiert, jeder weitere Lauf aktualisiert. Danach heißt der Befehl /coach.
# Kopiert NUR den Skill nach ~/.claude/skills/coach. Keine Agenten-Dateien, keine Einstellungen.
set -euo pipefail

REPO_URL="${COACHING_TEAM_REPO_URL:-https://github.com/sebaskauf/coaching-team.git}"
DATEN="${COACHING_TEAM_HOME:-$HOME/.coaching-team}"
QUELLE="$DATEN/repo"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ZIEL="$CLAUDE_DIR/skills/coach"

command -v git >/dev/null 2>&1 || { echo "git fehlt. Mac: xcode-select --install · Windows: https://git-scm.com" >&2; exit 1; }

# Schutz zuerst: nichts überschreiben, was nicht vom Coaching-Team stammt
if [ -d "$ZIEL" ] && [ ! -f "$ZIEL/.coaching-team" ]; then
  echo "Abbruch: $ZIEL gibt es schon und stammt nicht vom Coaching-Team. Nichts wurde verändert." >&2
  echo "Benenne den Ordner um (z. B. coach-alt) und starte die Installation noch einmal." >&2
  exit 2
fi

mkdir -p "$DATEN"
if [ -d "$QUELLE/.git" ]; then
  git -C "$QUELLE" pull --ff-only -q
  echo "Coaching-Team aktualisiert ($QUELLE)."
else
  git clone -q --depth 1 "$REPO_URL" "$QUELLE"
  echo "Coaching-Team heruntergeladen ($QUELLE)."
fi

mkdir -p "$CLAUDE_DIR/skills"
rm -rf "$ZIEL.neu"
cp -R "$QUELLE/skills/coach" "$ZIEL.neu"
rm -rf "$ZIEL"
mv "$ZIEL.neu" "$ZIEL"

echo "Installiert: Skill /coach in $ZIEL (Version $(cat "$ZIEL/.coaching-team"))."
echo "Tests: cd \"$QUELLE\" && python3 -m unittest discover -s tests -v"
echo "Erscheint /coach nicht sofort: /reload-skills eintippen oder Claude Code einmal neu starten."
