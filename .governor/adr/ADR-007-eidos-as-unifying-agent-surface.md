---
id: "ADR-007"
type: "decision"
title: "eidos-cli is the unifying agent surface; five forge packages become libraries"
status: "accepted"
date: "2026-05-14"
---

## Context

The conceptual source for this ADR is [THE-EIDOS](../../../eidos-philosophy/THE-EIDOS.md), authored alongside it. The architectural claim there is that an *eidos* — a unit of purpose defined by its telos — is what an agent operates on. The eidos contains one Pod (Rhea, 1–3 models), up to four activated forges (Research, Governor, Docket, Praxis), and a membership of code repositories. Eidi compose recursively via promoted child eidi.

The codebase today does not match this. Five separately-shipped Python packages (`telos-md` v0.4.1, `research-md` v0.5.1, `governor-md` v0.4.1, `docket-md` v0.4.1, and the unreleased `praxis-md` renamed from `hone`) each expose their own CLI and their own MCP server. ADR-006 collapsed each individual MCP surface to one `help` tool, which was the right move at the forge layer. But it left the *agent-facing* surface fragmented: an agent must learn five `mcp__*__help` entry points, and the on-disk shape is five heterogeneous top-level directories (`.telos/`, `.research/`, `.governor/`, `.docket/`, `.hone/`) with no "this is one eidos" container.

The architecture says the unit is the eidos. The CLI does not yet reflect that. The eidos data on disk does not yet reflect that. Storage is currently per-repo, which breaks for eidi that operate across multiple repositories — the antipattern of solutions spread across repos.

This ADR commits the architecture to code.

## Decision

We commit the following:

1. **`eidos-cli` is the unified agent-facing CLI for the scope architecture.** The binary name is `eidos`. It is the entry point for an agent or human operating on eidi. Verbs include `define`, `enter`, `status`, `spawn`, `activate`, `tick`, `close`, plus namespaced subcommand groups (`eidos telos`, `eidos research`, `eidos governor`, `eidos docket`, `eidos praxis`) for forge-specific operations.

2. **The five forge packages remain as Python libraries.** `telos-md`, `research-md`, `governor-md`, `docket-md`, `praxis-md` continue to be separately versioned and PyPI-published. Their pure-logic modules (`_logic/`) are consumed by `eidos-cli` directly — no subprocess overhead, no invented protocol. Their standalone CLIs continue to work for library users and tests, but they are no longer the primary agent surface.

3. **The five `mcp__*__help` servers retire in favor of one `mcp__eidos__help`.** Razor-thin still: one MCP tool, one description, one subcommand-drill-down argument. The deprecation path: keep the five servers operational through one minor version with deprecation notices in their `help` output; sweep consumers to `mcp__eidos__help` via `eidos migrate`; retire the five servers in the version after.

4. **On-disk layout is `.eidos/` per the THE-EIDOS specification.** A single `.eidos/` directory per eidos, living in the eidos's *home directory* — which is *not* tied to any specific code repository. The eidos.json manifest names which repos are members. Each member repo carries a `.eidos-pointer` (one line, gitignored) pointing at the eidos home. Child eidi nest at `<eidos-home>/.eidos/children/<id>/.eidos/` recursively.

5. **`governor.vision` retires.** The Telos forge owns the destination artifact — the four-field telos contract (`statement / success_when / failure_when / success_when_not`). Governor holds *contracts that honor the telos*: goals, guardrails, SOPs, ADRs. The fields are not duplicated. ADR-006's distinction between telos-md and governor-md as separate packages stands; what changes is that governor no longer claims any "vision" field — that artifact has a single home.

6. **`praxis-md` ships as the renamed `hone` package, from the start in the new shape.** Not as a separately MCP-served tool, but as the praxis forge consumed by `eidos-cli`. Hone's verbs (`tick`, `write-turn`, `notebook`, `status`) become praxis-md verbs accessible as `eidos praxis ...`. `failure_when_not` from the telos contract has its home in praxis-md as a `drift_category`, not in telos-md.

7. **`eidos migrate` is the consumer migration verb.** Idempotent. Consolidates existing heterogeneous `.telos/`, `.research/`, `.governor/`, `.docket/`, `.hone/` directories into a single `.eidos/`. For multi-repo cases, prompts the user to choose an eidos home directory and writes `.eidos-pointer` files into member repos. Single-repo cases default to the current repo as the home and operate in place.

8. **`eidos-cli`'s existing verbs migrate from Click to Typer.** Today `eidos-cli` is a small Click-based gateway (`login / logout / status / vault / health`). The new scope verbs are Typer-shaped, matching the rest of the trilogy's surface. Click → Typer is a one-time migration; the resulting CLI is consistent throughout.

The Python implementation lands now. The eventual Rust port (per `project_eidos_cli_and_kai` memory) is a mechanical translation; the design lives in THE-EIDOS, not in the language. No code in this ADR — it commits the direction, not the implementation. The build plan follows in a separate plan once the doctrine is read with fresh eyes.

## Consequences

**For consumers** (agents and humans using eidos-cli):
- New verbs: `eidos define`, `eidos enter`, `eidos status`, `eidos spawn`, `eidos activate`, `eidos tick`, `eidos close`.
- Existing forge verbs accessible as `eidos <forge> <verb>` (e.g., `eidos research finding-create`).
- Existing `mcp__*__help` MCP tools continue to function through one minor version, then retire. The single `mcp__eidos__help` is the long-term agent surface.
- Existing `.telos/`, `.research/`, `.governor/`, `.docket/`, `.hone/` directories must be consolidated via `eidos migrate` once the new shape ships. Idempotent; safe to run repeatedly; dry-run by default.
- Multi-repo workflows become first-class: declare member repos at `eidos define`; the eidos home holds all artifacts; member repos carry only `.eidos-pointer`.

**For package authors and the trilogy ecosystem:**
- The five Python packages stay separately versioned and PyPI-published. Their pure-logic modules become library APIs consumed by `eidos-cli`. Their standalone CLIs and MCP servers continue to work — deprecated but not broken — for backward compatibility through the next minor version.
- `governor.vision-set` / `governor.vision-view` are removed. Consumers using these are migrated by `eidos migrate` to the Telos forge's four-field artifact.
- `hone` is renamed to `praxis-md` (PyPI package, CLI binary, MCP server, state directory `.hone/` → `.praxis/`). The migrate script handles the in-place rename for existing consumers.

**For MCP hosts:**
- A single MCP entry to register: `mcp__eidos__help`. Other entries should be removed after the one-minor-version transition.
- The forge-specific `help` tools (e.g., `mcp__telos__help`) continue to respond during deprecation but emit a notice in their text content directing consumers to `mcp__eidos__help`.
- Bash patterns for consumer allowlists: a single `Bash(eidos:*)` replaces the five `Bash(telos-md:*)`, `Bash(research-md:*)`, etc.

**For the architecture:**
- `mcp__eidos__help` becomes the single discovery surface across the entire scope architecture. Five tool descriptions in session-start prompts collapse to one — a follow-on to ADR-006's 88-tools-to-1 win, applied at the next compositional layer.
- The eidos manifest (`eidos.json`) is the durable record of an eidos's identity, membership, activated forges, and parent linkage. It is the single source of truth for cross-forge integrity.
- Recursion via `eidos spawn` is the only mechanism for adding governance scope below the project root. Goals do not implicitly recurse; they must be explicitly promoted. This bounds the system's complexity to what has been deliberately chosen.

## What this ADR does not commit

- A timeline. The build plan follows separately. This ADR commits direction.
- The Rust rewrite of `eidos-cli`. Python first; Rust later, per memory.
- Cross-eidos learning propagation mechanism. Real gap; deferred to a follow-on doc.
- Cross-scope auditor pattern for `failure_when` enforcement. Deferred.
- The temporal lifetime semantics of eidi — when does one die / merge / fork beyond the verbs above. Deferred.

These deferrals are intentional. This ADR is large enough on its own; the deferred items are independent design questions that can land in their own ADRs without blocking this one.

## References

- [THE-EIDOS](../../../eidos-philosophy/THE-EIDOS.md) — conceptual source
- [THE-POD](../../../eidos-philosophy/THE-POD.md) — bounded-cardinality concession (Solo / Pair / Pod)
- [THE-FORGE](../../../eidos-philosophy/THE-FORGE.md) — each operational layer is a forge
- [THE-FRACTAL](../../../eidos-philosophy/THE-FRACTAL.md) — composition for scale
- [THE-ACCOUNTABILITY-CHAIN](../../../eidos-philosophy/THE-ACCOUNTABILITY-CHAIN.md) — forge → contract → Pod inside an eidos
- [ADR-006](./ADR-006-cli-first-razor-thin-mcp.md) — the precursor at the per-package layer
