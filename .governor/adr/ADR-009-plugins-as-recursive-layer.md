---
id: "ADR-009"
type: "decision"
title: "Plugins are the recursive layer; the CLI engine stays small"
status: "accepted"
date: "2026-05-14"
---

## Context

[ADR-007](ADR-007-eidos-as-unifying-agent-surface.md) committed `eidos-cli` as the unified agent surface. [ADR-008](ADR-008-eidos-do-orchestrating-engine.md) committed `eidos do` as the orchestrating engine that runs THE-LOOP for a docket task. Both ADRs treated the CLI as a fixed set of primitives.

In conversation on 2026-05-14, we found a piece of doctrine those ADRs do not yet express: **learnings → plugins is the cross-eidos compounding mechanism, and the verb that performs that promotion (`eidos learn`) is itself a candidate to be a plugin, not a primitive.**

The brief at `cockpit-eidos/briefs/2026-05-14-eidos-as-unified-agent-surface.md` left "cross-eidos learning propagation" as an open risk. That risk closes here. The mechanism is the plugin store: a pattern lifted out of one eidos's praxis turns becomes a plugin available to every other eidos. `~/.eidos/plugins/<slug>/` is the propagation surface.

The natural instinct, on first encountering this, is to add a top-level `eidos learn` verb to the engine. That instinct is wrong, because:

- The *quality of promotion* — what makes a praxis turn worth promoting, what fields the plugin manifest needs, what synthesis pattern produces the best playbook — is exactly the kind of thing the system should improve at over time. If `learn` is hardcoded in the engine, every improvement requires shipping a new `eidos-cli` release. If `learn` is a plugin, running `eidos learn` against praxis turns *about plugin-promotion sessions* emits a better `learn` plugin. The system becomes self-improving at the plugin layer.

- The engine should hold primitives. Patterns belong in plugins. The test of "is this a primitive": *does shipping a better version of this behavior require a CLI release?* If yes, primitive. If no, plugin.

- THE-FRACTAL says the pattern repeats at every scale. ADR-007 applied it to eidi (eidi recurse via child eidi). This ADR applies it to the CLI itself: the engine is the fixed substrate; plugins are the recursive layer where the system improves itself.

This ADR commits that boundary to code.

## Decision

We commit the following:

1. **The `eidos` CLI engine stays small.** Primitives are: `define`, `enter`, `status`, `activate`, `close`, `tick`, `do`, `spawn`, `migrate`, the forge namespaces (`telos`, `research`, `governor`, `docket`, `praxis`), `auth`, `vault`, `health`, `mcp serve`, plus the plugin runtime listed below. Nothing else is a primitive without an explicit ADR amendment.

2. **The plugin runtime is the minimal bootstrap.** Four verbs: `eidos plugin list`, `eidos plugin install <path|url>`, `eidos plugin run <slug> [args...]`, `eidos plugin show <slug>`. That is the entire engine-side plugin surface. Everything plugin-related beyond loading and running is itself implementable as a plugin.

3. **Plugin shape:**
   ```
   plugins/<slug>/
     plugin.yaml      # metadata: slug, version, description, when_to_fire conditions, owner_forge, required_evidence
     playbook.md      # the substrate-readable procedure (this is the prompt)
     verify.py        # optional gate (Python; runs after substrate ACT, returns pass/fail + reasons)
     examples/        # optional sample inputs + sample outputs
   ```

4. **Two-tier plugin store with local precedence:**
   - Eidos-local: `<eidos_home>/.eidos/plugins/<slug>/` — applies to one eidos only.
   - User-global: `~/.eidos/plugins/<slug>/` — applies across every eidos this user operates.
   - Lookup order: eidos-local first, user-global second. The same slug in both lets an eidos override the global definition.

5. **`learn` is the first plugin, shipped embedded in the wheel.** On first run, `eidos plugin run learn` copies the bundled `learn` definition from the wheel into `~/.eidos/plugins/learn/`. From then on, the user owns it and can edit it. Subsequent installs of `eidos-cli` do not overwrite it; bundled-version drift is surfaced to the user via `eidos plugin show learn`.

6. **Top-level command aliasing.** Installed plugins may register a top-level alias such that `eidos learn` resolves to `eidos plugin run learn`. The alias table is computed at CLI startup by scanning the two plugin stores. Conflicts with engine primitives are *rejected* — primitives win, plugins must pick a non-colliding slug. Aliases appear in `eidos --help` under a separate "Plugins" section.

7. **The plugin candidate ledger from ADR-008 feeds `learn`.** `orchestrator/learn.py::log_plugin_candidate` already counts observations against the threshold (≥3 obs + ≥2 verified + ≥1 failure analysis). When the threshold is crossed, the candidate appears in `eidos plugin list --candidates`. The `learn` plugin reads that list, plus any explicitly-named praxis turn ids, and produces a draft plugin manifest for the user to review and accept.

8. **Active and passive promotion paths share the same destination.**
   - Active: `eidos learn --from-praxis TURN-ID` or `eidos learn --candidate <slug>` — user-initiated.
   - Passive: candidate ledger crosses threshold; surfaces in `eidos plugin list --candidates` until promoted.

9. **Cross-eidos learning propagation IS the user-global plugin store.** No new mechanism. `~/.eidos/plugins/` is the propagation surface, populated by `learn` and consumed by every eidos's `eidos do` loop during PERCEIVE (which now reads applicable plugins as additional context per their `when_to_fire` conditions).

## Consequences

**For the engine:**
- `eidos-cli` v1.0 ships with the plugin runtime (4 verbs) and the bundled `learn` plugin. No other engine work blocks on this ADR.
- The CLI grows narrower over time, not wider. Anything currently in the engine that *could* be a plugin is now a refactor candidate; nothing is immediately yanked, but the next time we touch any such verb, we ask the primitive-test question.
- TASK-0009 (plugin system) on the eidos-cli-v1 docket becomes the immediate priority work after the v1.0 cut.

**For the loop:**
- `eidos do`'s PERCEIVE phase gains a plugin lookup: scan both plugin stores, match against the task's owner_forge and tags, attach matching playbooks to the context bundle as additional substrate input. The substrate decides whether to follow a playbook. The engine doesn't enforce; plugins are advisory unless their `verify.py` says otherwise.
- VERIFY may delegate to a plugin's `verify.py` when the task names that plugin in its frontmatter. High-stakes operations may *require* a plugin to be applied (e.g., release tasks require the `release-checklist` plugin's verify to pass). That requirement is expressed in the task's frontmatter, not the engine.

**For consumers:**
- The brief's open risk on cross-eidos learning propagation closes. Plugin store is the mechanism. Update the brief accordingly.
- The plugin candidate threshold from ADR-008 now has a destination — promotion via `learn` — so the threshold is no longer a wired-but-unused gate.

**What this ADR does not commit:**
- The plugin manifest schema is sketched but not frozen; the `learn` plugin's first job is to converge on a schema by promoting real praxis turns.
- Plugin sharing between users (registry server, signing, trust) is deferred. v1.0 plugins move via file paths and git repos.
- The `claude -p` / Agent SDK substrate that actually runs a plugin's playbook is per [global instructions](../../../../.claude/CLAUDE.md) — fixed-cost tools only; no direct `anthropic` SDK use.

**Bootstrap problem:** addressed by the wheel-bundled `learn` plugin. After v1.0 ships, every plugin-related operation that isn't one of the four runtime primitives can itself be a plugin. The system is then self-extending.

## Relations

- [ADR-007](ADR-007-eidos-as-unifying-agent-surface.md) — committed the unified surface; this ADR sets the boundary between engine and plugins inside that surface.
- [ADR-008](ADR-008-eidos-do-orchestrating-engine.md) — defined the loop and the plugin candidate ledger; this ADR gives the ledger a destination.
- [THE-FRACTAL](../../../eidos-philosophy/THE-FRACTAL.md) — the pattern this ADR applies to the CLI/plugin boundary.
- [THE-EIDOS](../../../eidos-philosophy/THE-EIDOS.md) — the architectural source; plugins are the cross-eidos compounding layer it implies but does not yet name.
- Brief `cockpit-eidos/briefs/2026-05-14-eidos-as-unified-agent-surface.md` — open risk on learning propagation closes here.
