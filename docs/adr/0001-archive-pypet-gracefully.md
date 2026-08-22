# ADR 0001: Archive pypet gracefully

- Status: Accepted
- Date: 2026-08-22
- Decided in: [wayfinder map #70](https://github.com/fabiandistler/pypet/issues/70), locked via [#74](https://github.com/fabiandistler/pypet/issues/74)

## Context

pypet is a dormant TOML-backed CLI snippet manager for terminal recall and
parameterized command execution. Its maintainer's daily work now flows through
coding agents (Claude Code, Codex CLI, OpenCode), which removed most of the
*recall* need for stored snippets.

The working hypothesis was that a *curation* need might remain: vetted,
parameterized commands shared across machines and consumable by agents.
Three research tickets tested this against reality:

- **Usage footprint** (~72 installs/month, no external community): archiving
  costs nobody but the maintainer anything.
- **Landscape**: the agent-era niche is real but narrow and contested — Atuin
  has pivoted into it with momentum and ships MCP support; pet/navi remain
  human-recall tools; devs hand-curate CLAUDE.md.
- **MCP feasibility**: technically easy (local stdio servers, official Python
  SDK, ~weekend for read-only tools), but moot without personal pull.

The pre-agreed gate was the personal pull test: could the maintainer name a
concrete moment in the last month where pypet's curation was missed? It could
not be named. The only remaining demand signal is gone.

## Decision

**Archive pypet gracefully.** Cut one final release, hand over at the top of
the README, then flip GitHub's Archive flag.

## Alternatives considered

- **Continue as agent-facing curated command library (MCP server)** — the
  strongest technical direction: feasible, small, differentiated. Rejected:
  zero personal pull fails the agreed gate, and Atuin already occupies the
  niche with more momentum than a solo restart can muster.
- **Zombie mode** (no releases, repo lingers unarchived) — rejected: worst of
  both worlds; signals false activity while rotting.

## Sunset criterion applied

Archive unless a direction clearly beats "archive + handover doc" on both
personal pull and external demand. Neither held.

## Coarse roadmap

Milestone-level only; implementation is a future effort.

1. **Final release** — cut `v0.9.0` from current main via `scripts/release.sh`
   with the README carrying an archived/unmaintained banner (the PyPI
   description derives from the README). Existing features freeze as-is;
   no deprecation work.
2. **Handover section at top of README** — archived-as-of date; alternatives:
   Atuin (agent-era command management with built-in MCP), pet/navi (classic
   human recall); note that `~/.config/pypet/snippets.toml` is plain TOML and
   stays portable as-is — nothing to export or migrate.
3. **Flip GitHub's Archive flag** after the final release ships. Unarchiving
   later is one click if revived.

## Consequences

- The TOML store remains a stable, portable artifact; users lose nothing.
- pypet receives security fixes only if revived; the archive flag makes its
  status unambiguous to passers-by.
- Revival would be a fresh effort with its own ADR, not a resumption.
