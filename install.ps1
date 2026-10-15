# Coaching-Team: Kopier-Installation für Claude Code unter Windows (PowerShell).
# Erster Lauf installiert, jeder weitere Lauf aktualisiert. Danach heißt der Befehl /coach.
# Kopiert NUR den Skill nach %USERPROFILE%\.claude\skills\coach. Keine Agenten-Dateien, keine Einstellungen.
$ErrorActionPreference = "Stop"
$RepoUrl = if ($env:COACHING_TEAM_REPO_URL) { $env:COACHING_TEAM_REPO_URL } else { "https://github.com/sebaskauf/coaching-team.git" }
$Daten = if ($env:COACHING_TEAM_HOME) { $env:COACHING_TEAM_HOME } else { Join-Path $HOME ".coaching-team" }
$Quelle = Join-Path $Daten "repo"
$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
$Ziel = Join-Path $ClaudeDir "skills\coach"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Error "git fehlt. Installation: https://git-scm.com"; exit 1 }

if ((Test-Path $Ziel) -and -not (Test-Path (Join-Path $Ziel ".coaching-team"))) {
  Write-Error "Abbruch: $Ziel gibt es schon und stammt nicht vom Coaching-Team. Nichts wurde verändert. Benenne den Ordner um und starte die Installation noch einmal."
  exit 2
}

New-Item -ItemType Directory -Force -Path $Daten | Out-Null
if (Test-Path (Join-Path $Quelle ".git")) {
  git -C $Quelle pull --ff-only -q
  Write-Output "Coaching-Team aktualisiert ($Quelle)."
} else {
  git clone -q --depth 1 $RepoUrl $Quelle
  Write-Output "Coaching-Team heruntergeladen ($Quelle)."
}

New-Item -ItemType Directory -Force -Path (Join-Path $ClaudeDir "skills") | Out-Null
if (Test-Path $Ziel) { Remove-Item -Recurse -Force $Ziel }
Copy-Item -Recurse (Join-Path $Quelle "skills\coach") $Ziel

Write-Output "Installiert: Skill /coach in $Ziel (Version $((Get-Content (Join-Path $Ziel '.coaching-team')).Trim()))."
Write-Output "Tests: cd `"$Quelle`"; python -m unittest discover -s tests -v"
Write-Output "Erscheint /coach nicht sofort: /reload-skills eintippen oder Claude Code einmal neu starten."
