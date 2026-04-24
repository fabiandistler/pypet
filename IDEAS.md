# pypet — Modernization Ideas

Brainstorm zur Frage: Wie bleibt pypet relevant, wenn Entwickler:innen
zunehmend mit KI-Agents statt direkt im Terminal arbeiten?

Leitgedanke: pypet positioniert sich nicht als Konkurrenz zu KI-Agents,
sondern als **persönliche und Team-Wissensschicht**, die Agents nutzen können.

---

## Idea 1 — pypet als MCP-Server für KI-Agents

Status: **In Planung** (siehe `openspec/changes/2026-04-24-add-mcp-server/`)

Stellt die pypet-Snippet-Bibliothek via Model Context Protocol für KI-Agents
(Claude Code, Cursor, Copilot CLI etc.) zur Verfügung. Der Agent bekommt
Tools wie `pypet_search`, `pypet_get`, `pypet_list_by_tag`.

**Warum stark:** Der Agent kennt die persönlichen Vorlieben des Users —
kubectl-Kombinationen, Docker-Cleanup-Patterns, projektspezifische
Build-Befehle. pypet wird zum Langzeitgedächtnis über Agent-Sessions hinweg.

**Bonus:** Die bestehende `gen`-Funktion könnte mittelfristig redundant
werden (Agents generieren ohnehin), aber `save` und die Snippet-Bibliothek
selbst werden dadurch zum Premium-Feature.

---

## Idea 2 — Auto-Capture aus Agent-Sessions ("Learn Mode")

Status: **Idee**

Gegenrichtung zu Idea 1: Wenn ein KI-Agent im Terminal einen komplexen
Befehl erfolgreich ausführt (verzwickter `ffmpeg`- oder `awk`-One-Liner),
bietet pypet an, ihn zu speichern — inklusive dem natürlichsprachlichen
Kontext aus dem ursprünglichen Prompt.

**Konkret:** Shell-Hook oder Agent-Plugin, das erkennt: "hier wurde gerade
etwas Nicht-Triviales ausgeführt, exit code 0, lief ungewöhnlich
lange/hatte viele Flags" → `pypet save-last --from-agent "der Prompt, der
dazu führte"`. Beim nächsten Mal findest du es per Naturtext-Suche wieder,
ohne den Agent dafür überhaupt zu bemühen.

**Warum stark:** Löst das Problem, dass Agents oft dieselben Probleme
immer wieder von Null lösen. Du baust dir passiv eine kuratierte
Snippet-Bibliothek, ohne aktiv daran zu denken.

---

## Idea 3 — Projekt-/Team-Runbooks statt globaler Snippet-Liste

Status: **Idee**

Weg von "eine große Liste persönlicher Befehle", hin zu projektgebundenen,
ausführbaren Runbooks. Eine `.pypet/` im Repo, die dem Team (und ihren
Agents) sagt: "So deployed man hier, so testet man E2E, so rollt man
zurück."

**Konkret:** `pypet init` im Repo, Snippets werden mit Repo
mitversioniert. Onboarding eines neuen Devs wird `pypet list` statt
200-Seiten-Confluence-Dokument. Kombiniert mit Idea 1 bekommt der Agent
eines neuen Devs sofort Zugriff aufs Team-Wissen.

**Warum stark:** Das ist ein Problem, das Agents *nicht* lösen — sie
halluzinieren gerne projektspezifische Details. Ein autoritatives,
commit-bares Runbook-Format füllt diese Lücke.

---

## Reihenfolge

1. **Idea 1** zuerst — kleinster Scope (Wrapper um bestehende Commands),
   positioniert das Tool aber sofort neu im KI-Ökosystem.
2. **Idea 3** als nächster strategischer Pivot (verändert das
   Datenmodell: globale Snippets → projekt-gescopte Snippets).
3. **Idea 2** als Komfort-Feature, sinnvoll erst wenn 1 + 3 stehen.
