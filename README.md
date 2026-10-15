# Coaching-Team für Claude

Fünf Claude-Agenten arbeiten zusammen wie ein komplettes Coaching-Team: Trainingsplan, Kalorien per Foto, Form-Check per Foto und ein wöchentlicher Check-in. Kostenlos, MIT-Lizenz, auf Deutsch.

**Anleitung mit Bildern:** https://coach.skaile.de

## 1. Was es ist

| Agent | Was er macht |
|---|---|
| **Analyse-Agent** | checkt in 5 kurzen Fragenblöcken, wo du stehst und was dein Ziel ist, und rechnet Kalorien- und Proteinziel aus |
| **Trainings-Agent** | baut deinen Trainingsplan, im Studio oder zu Hause, mit klarer Steigerungsregel |
| **Ernährungs-Agent** | du fotografierst dein Essen, er schätzt Kalorien und Makros und sagt dir, wo du heute stehst |
| **Form-Agent** | schaut sich ein Foto deiner Übung an und sagt dir, was du an deiner Haltung verbessern kannst |
| **Check-Agent** | fragt dich jede Woche, wie es lief, und passt deinen Plan an deinen Fortschritt an |

Ein Chef verteilt deine Nachrichten an den richtigen Agenten. Dein Stand steht in einer **Coaching-Akte**, damit dein Team nichts vergisst.

## 2. In der Claude-App starten (empfohlen, ohne Technik)

1. Lade [`app/coaching-team.txt`](app/coaching-team.txt) herunter.
2. Öffne [claude.ai](https://claude.ai) und leg ein neues Projekt an, Name: **Mein Coaching-Team**.
3. Kopier den Text aus [`app/projekt-anweisungen.txt`](app/projekt-anweisungen.txt) in die Anweisungen des Projekts und füg die Datei `coaching-team.txt` zu den Projektdateien hinzu.
4. Starte im Projekt einen neuen Chat und schreib: `Start`
5. Optional: [`app/check-in-sonntag.ics`](app/check-in-sonntag.ics) öffnen, dann erinnert dich dein Kalender jeden Sonntag um 18 Uhr an den Check-in.

Danach läuft alles auch in der Claude-App am Handy, im selben Projekt. Die Schritte mit Bildern stehen auf https://coach.skaile.de.

## 3. Claude Code: Installation

**Empfohlen: Lass Claude das machen.** Füge in Claude Code ein:

```
Richte mir bitte das Coaching-Team ein: https://github.com/sebaskauf/coaching-team
```

Claude führt dann diese Befehle aus.

**Mac und Linux:**

```bash
[ -d ~/.coaching-team/repo/.git ] || git clone --depth 1 https://github.com/sebaskauf/coaching-team.git ~/.coaching-team/repo
bash ~/.coaching-team/repo/install.sh
```

**Windows (PowerShell):**

```powershell
if (-not (Test-Path "$HOME\.coaching-team\repo\.git")) { git clone --depth 1 https://github.com/sebaskauf/coaching-team.git "$HOME\.coaching-team\repo" }
powershell -ExecutionPolicy Bypass -File "$HOME\.coaching-team\repo\install.ps1"
```

Das Skript kopiert nur den Skill nach `~/.claude/skills/coach`, sonst nichts. Gibt es dort schon einen fremden Ordner `coach`, bricht es ab und verändert nichts. Danach heißt der Befehl `/coach`. Erscheint `/coach` nicht sofort, tippe `/reload-skills` oder starte Claude Code einmal neu. **Update:** denselben Befehl noch einmal ausführen.

**Tests:**

```bash
cd ~/.coaching-team/repo && python3 -m unittest discover -s tests -v
```

**Alternative als Plugin** (selbst in Claude Code eintippen):

```
/plugin marketplace add sebaskauf/coaching-team
/plugin install coaching-team@coaching-team
```

Als Plugin heißt der Befehl `/coaching-team:coach`.

Deine Daten liegen in Claude Code im Ordner `mein-coaching/` dort, wo du `/coach` startest: `akte.md`, `verlauf.csv`, `essen/`, `training/`, `form/`.

## 4. Befehle

| In der App schreibst du | In Claude Code | Wer übernimmt |
|---|---|---|
| `Start` | `/coach start` | Analyse-Agent, danach Trainings-Agent |
| `Training heute` · `Training fertig: Kniebeuge 3×10 mit 40 kg` | `/coach heute` · `/coach plan` | Trainings-Agent |
| Foto + `Was hab ich gegessen?` · `Tagesbilanz` | `/coach essen` · `/coach bilanz` | Ernährungs-Agent |
| Foto + `Check meine Form` | `/coach form` | Form-Agent |
| `Check-in` | `/coach check` | Check-Agent |
| `Neues Ziel` | `/coach start` | Analyse-Agent |
| `Hilfe` | `/coach hilfe` | Übersicht |

## 5. Was es nicht ist

- **Kein Arzt, kein Physio.** Bei Schmerzen ersetzt dein Team die Übung. Anhaltende Schmerzen, Vorerkrankungen, Medikamente oder Schwangerschaft bitte ärztlich abklären.
- **Kalorien aus Fotos sind Schätzungen** mit Spanne. Öl, Saucen und Getränke sieht man oft nicht. Etikett mitfotografieren = echte Werte.
- **Ein Foto zeigt einen Moment, keine Bewegung.** Der Form-Agent bewertet nur, was zu sehen ist.
- **Claude schreibt dich nicht von selbst an.** Die Erinnerung zum Check-in kommt über deinen Kalender.
- Die Richtwerte (Mifflin-St Jeor, 1,6–2,2 g Protein pro kg, 10–20 Sätze pro Muskel und Woche) sind Standard-Richtwerte der Sportwissenschaft für gesunde Erwachsene, keine Garantie.

## 6. Datenschutz

Alles bleibt in deinem eigenen Claude-Konto (App) bzw. auf deinem eigenen Rechner (Claude Code). Dieses Repo sammelt keine Daten und schickt nichts irgendwohin. Körperfotos sind nie nötig.

## 7. Aufbau

```
skills/coach/          einzige Quelle aller Inhalte (Chef, 5 Agenten, Wissen, Akte, Tools)
app/                   erzeugt von tools/bundle.py, nie von Hand ändern
tools/bundle.py        baut app/ aus skills/coach/
tests/                 Rechner, Kalender, Bundle, Installation
quellen/               Herkunft der Nährwerte (Bundeslebensmittelschlüssel 4.0)
```

Nur Python-Standardbibliothek, Python 3.8 oder neuer. Nährwerte: Bundeslebensmittelschlüssel 4.0 (Max Rubner-Institut, CC BY 4.0).

## 8. Lizenz

MIT. Gebaut von Sebastian Kauffmann (SKAILE).
