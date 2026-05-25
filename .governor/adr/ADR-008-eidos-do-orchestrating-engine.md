---
id: "ADR-008"
type: "decision"
title: "eidos do <task-id> — the orchestrating engine of the scope architecture"
status: "accepted"
date: "2026-05-14"
---

## Context

ADR-007 commits to ``eidos-cli`` as the unified agent surface for the scope architecture. The structural verbs (``define``, ``enter``, ``status``, ``activate``, ``tick``, ``close``, ``spawn``, ``migrate``) plus the forge namespaces (``eidos telos | research | governor | docket | praxis``) are landed or scoped for v1.0. The MCP surface (``mcp__eidos__help``) is razor-thin. The five forge libraries are eidos-aware via ``.eidos/<forge>/`` path resolution.

What's missing is the verb that *runs the discipline*. ADR-007 says eidos should not just track work — it should orchestrate it. The user named the behavior explicitly: *"When given a task, I don't want it to just do the task. I want it to study it, research, consider unknowns, consider gotchas, consider false premises, plan, ask another AI to opine (sometimes), act, verify, learn from the experience, document it in the system of record that's key for the system it was improving, and consider making a plugin for eidos itself to solve that problem in the future."*

That is THE-LOOP from eidos-philosophy applied at the per-task scope, with substantial structural support from the forges (research findings, governor contracts, docket execution, praxis learnings). The current ``eidos`` surface is *scaffolding for this verb to exist*. The verb itself doesn't yet.

This ADR commits the design.

## Decision

The canonical work-execution verb is ``eidos do <docket-task-id>``. **It is THE-LOOP at the per-task scope, with the canonical phase names from [THE-LOOP](../../../eidos-philosophy/THE-LOOP.md) preserved exactly.** Earlier drafts of this ADR coined a parallel vocabulary (STUDY/RESEARCH/ADVERSARIAL/PLAN/etc.) which obscured the doctrine. The vocabulary is now aligned.

### The phases

```
PERCEIVE    → load task + active telos + active guardrails (governor.guardrails)
              + relevant prior praxis turns (matched by task tags).
              Mostly mechanical: read what exists. THE-LOOP says PERCEIVE
              is reading, not deliberating.

[CARDINALITY PREFLIGHT]
              After PERCEIVE, before DECOMPOSE: cheap classifier evaluates
              the four escalation triggers against the task description +
              loaded context. Decides Solo / Pair / Pod for ALL subsequent
              phases. Each phase may locally override upward (never
              downward). This is what prevents Solo agents from doing
              hours of work and *then* asking for help — escalation is
              gated at entry, not at exit.

DECOMPOSE   → break the task into subtasks with explicit dependencies.
              Per THE-LOOP this is a routing decision, not a creative one.
              For trivial leaf tasks the decomposition is "one subtask,
              this task" and the loop body collapses to a single ACT.

SPECIALIZE  → for each subtask: retrieve relevant prior decisions
              (research forge), surface adversarial concerns (gotchas,
              unknown unknowns, false premises against the praxis pattern
              library), and select the appropriate capability/substrate.

ACT         → execute. Substrate is delegated; eidos do does not contain
              the intelligence. ACT must produce **verifiable evidence**
              alongside its output — test results, exit codes, diff artifacts,
              assertion logs. This is captured as the evidence bundle.

COMPRESS    → critical step omitted from earlier drafts. Per THE-LOOP,
              compression is the relay handoff that prevents context
              degradation. Each ACT produces a structured transition
              summary: what was produced, what matters for VERIFY, what
              would the agent do next. Without this, VERIFY operates on
              raw output and the system goes blind across long task chains.

[RECONCILE — implicit]
              Before VERIFY: reconcile the plan with what actually
              happened during ACT. Substrate-level deviations from the
              plan are surfaced here so VERIFY checks success (did we
              reach the telos's success_when?), not compliance (did we
              follow the plan?).

VERIFY      → check evidence against active forge contracts (deterministic
              gates). Check against telos.success_when (arrival),
              failure_when (dead), success_when_not (drift). For
              high-stakes operations (per the Solo-never-floor list in
              THE-POD), VERIFY fails *closed* — semantic uncertainty
              escalates to human or Pair review rather than passing on
              best-effort substrate judgment. This is THE-ACCOUNTABILITY-
              CHAIN's "evidence not vibes" rule, enforced.

LEARN       → write a praxis turn capturing the outcome (improved /
              no-op / reverted / blocked) and the delta. Route the
              durable artifacts to their system-of-record (the
              previously-named "DOCUMENT" step folds in here per
              THE-LOOP — LEARN is where outputs become structured memory).
              Log a plugin candidate if the task's pattern is novel
              (the previously-named "META" step folds in here too —
              candidates ARE a kind of learning, gated by frequency).

RETRY       → if VERIFY failed: the Pod (or Solo) re-enters with the
              error context, rotating roles per THE-POD's rotation-on-
              retry rule. Recursive self-repair. The retrier has no
              attachment to the failed proposal. Goes back to DECOMPOSE
              or SPECIALIZE, depending on where verification surfaced
              the failure.
```

The phase count is **8** (matching THE-LOOP's canonical form) plus the cardinality preflight. The earlier "10 phases" framing conflated execution phases with policy decisions (cardinality) and writeback steps (document, meta), which are not separate phases of work.

### The five durable artifacts (revised)

Per invocation, eidos do produces five durable artifacts. The earlier draft listed plugin-candidate as one of five; this is wrong — plugin candidates are *conditional* (only fire when a pattern is novel). The corrected core five:

1. **The plan** (.eidos/docket/plans/TASK-NNNN.md) — DECOMPOSE + SPECIALIZE output.
2. **The evidence bundle** (.eidos/docket/evidence/TASK-NNNN/) — the ACT output's verifiable proof: test results, logs, diff artifacts, exit codes. **This is the critical artifact for VERIFY**. Without it, verification is "vibes 2.0" (per the reviewers).
3. **The praxis turn** (.eidos/praxis/turns/<tick-id>.md) — LEARN's record: outcome, delta, lessons.
4. **The task completion** (.eidos/docket/completed/TASK-NNNN.md) — docket state transition.
5. **The system-of-record update** — wherever the SOR routing rules direct (docs, ADRs, external systems, or default to docket-only).

**The plugin candidate** is a *sixth, conditional* artifact — written to .eidos/praxis/patterns/candidates/ when the task's pattern is novel enough to warrant a candidate. Not produced every invocation. Promotion to actual plugin requires ≥ 3 distinct observations + ≥ 2 verified successes + ≥ 1 failure analysis, per-eidos configurable in governor.sops/plugin_promotion.md.

### Cardinality as preflight, not phase

Earlier draft put CARDINALITY after PLAN. Both reviewers correctly flagged this as too late: the cardinality decision must precede DECOMPOSE/SPECIALIZE because high-stakes / novel / ambiguous / undocumented tasks need different decomposition and adversarial review, not just different execution.

Corrected: cardinality is a **preflight gate** after PERCEIVE. The Solo-default policy from THE-POD is honored — the preflight is itself a Solo operation (single cheap LLM call against task description + telos + recent praxis), keeping the bounded-unit principle. Any phase may *override upward* (escalate from Solo to Pair, or Pair to Pod) if the work surprises. Phases never override downward; once Pod is convened, it stays for the remainder of the loop.

### The `--continue` continuation envelope

ACT happens in the calling substrate (not in eidos do's own process), and the verb returns after PLAN to be resumed by ``eidos do --continue <task-id>``. Codex correctly flagged this as a fragile split-brain state machine. The fix: every continuation requires a signed/hashed **continuation envelope** carrying:

- eidos id
- task id and version
- plan hash (SHA of .eidos/docket/plans/TASK-NNNN.md)
- SOR routing hash (SHA of governor.sops/sor_routing.md at planning time)
- member repo HEAD SHAs (per eidos.json.members)
- substrate label (which agent / model produced the plan)
- evidence bundle reference (path to ACT outputs)

On ``--continue``, eidos do verifies all hashes. If any mismatch, refuses with an explicit *stale-state* error and requires the user to re-run from DECOMPOSE. This eliminates the "ran plan on machine A, continued on machine B with different repo state, didn't notice" failure mode.

### SOR routing by artifact class, not tags-as-authority

Earlier draft routed the SOR update by task tags. Codex flagged this as too weak: tags are useful as *selectors* but should not be authority. Corrected scheme:

```yaml
# .eidos/governor/sops/sor_routing.md (front matter)
rules:
  - artifact_class: docstring_update
    owner_forge: docket
    target: relative_path_in_repo  # task must specify
    required_evidence: [diff, tests_pass]
    fallback: docket_completed_only
  - artifact_class: architectural_decision
    owner_forge: governor
    target: governor_adr_next_id  # auto-numbered
    required_evidence: [adversarial_review_log]
    fallback: research_finding_only
  - artifact_class: research_finding
    owner_forge: research
    target: research_findings_dir
    required_evidence: [sources_with_content_hash]
    fallback: docket_completed_only
  selectors:
    # tags map to artifact_classes — a hint, not authority
    docs: docstring_update
    documentation: docstring_update
    governance: architectural_decision
    research: research_finding
default_artifact_class: docket_completion_only
```

Artifact class names the *kind* of thing being produced; owner_forge names *which forge writes it*; target names the *concrete path*; required_evidence names *what must accompany the write for it to pass VERIFY*. Tags are downgraded to selectors that suggest an artifact class.

### Cardinality default policy (per THE-POD)

Already detailed in the phases section above as a **preflight gate after PERCEIVE**. The Solo-never-floor list from THE-POD applies: telos creation/supersession, guardrail creation, ADR acceptance, failure_when→close, promotion to child eidos, closing with outcome=reached — these always require ≥ Pair, regardless of the preflight classifier's verdict. When ``eidos do`` invokes any of these as part of executing a task, the local override fires automatically.

### Plugin candidate logging — bounded promotion (resolves TASK-0009 contract)

The earlier draft set promotion threshold at "≥ 3 observations." Both reviewers correctly flagged that this is fine for *candidate logging* but too low to be a *promotion signal*. Patterns that fire 3 times in one repo are anecdote, not evidence.

Corrected: candidate logging at observation 1; **promotion gate** requires:

- ≥ 3 distinct observations (across task IDs, not just invocations)
- ≥ 2 verified successful outcomes (the pattern actually helped)
- ≥ 1 failed or near-miss analysis (the pattern's failure mode is understood)

Per-eidos overridable via ``.eidos/governor/sops/plugin_promotion.md``. Default thresholds above; some eidi may want stricter (≥ 5 obs / 3 verified / 2 failures) for high-stakes domains.

A plugin candidate record at ``.eidos/praxis/patterns/candidates/<pattern-id>.md``:

```yaml
---
pattern_id: <slug>
observations:
  - {task_id: TASK-NNNN, date: <iso>, outcome: improved}
  - {task_id: TASK-MMMM, date: <iso>, outcome: improved}
  - {task_id: TASK-PPPP, date: <iso>, outcome: blocked, analysis: <ref>}
first_seen: <iso>
last_seen: <iso>
task_class: <free-form>
proposed_plugin: <one-line>
promotion_status: candidate  # candidate | promoted | rejected
---
```

Cross-eidos pattern aggregation (so a pattern observed in 3 different eidi has more signal than 3× in one eidos) is a v1.1 task — see "Deferrals" below.

### High-stakes VERIFY fails closed

Codex's correct critique: deferring real Rhea/Pod semantic verification is only acceptable *if* high-stakes VERIFY fails closed into human or Pair review. Otherwise the doctrine drift — ADR-008 would silently pass best-effort substrate judgment on operations THE-ACCOUNTABILITY-CHAIN says require evidence.

Corrected: when VERIFY runs against an operation in the Solo-never-floor list, semantic uncertainty (substrate confidence below a threshold, or contradictory signals from forge contracts) **must** escalate. Either:

- A Pair review fires (a second model evaluates the evidence), or
- Human review is requested (the eidos surfaces "VERIFY blocked: <reason>; human/Pair sign-off required" and pauses)

It does not pass on Solo judgment for these operations. This is what makes the v1.0 implementation honest while waiting for Rhea-class real-time substrate.

### What runs Solo today; what waits for Rhea

In the v1.0 implementation:

- **PERCEIVE** is mechanical (file reads). No substrate needed.
- **Cardinality preflight** is a single cheap Solo call against task description + telos + recent praxis. Output: Solo / Pair / Pod for the rest of the loop.
- **DECOMPOSE / SPECIALIZE / ACT**: delegated to the calling substrate (the agent running ``eidos do`` — a Claude Code session, a Codex session, etc.). ``eidos do`` doesn't fork its own substrate in v1.0; it relies on the calling agent's intelligence at the cardinality the preflight selected.
- **COMPRESS** is a single substrate call at the chosen cardinality.
- **VERIFY**: forge-contract checks are deterministic (Python-level assertions). Semantic checks against telos triggers run at the chosen cardinality; for high-stakes ops they fail closed per the rule above. Real Pod (Rhea-class) verification waits for substrate latency to drop.
- **LEARN**: writes praxis turn deterministically. Outcome classification (improved/no-op/reverted/blocked) is agent-provided; later, Pod-classified.
- **RETRY** uses the calling substrate, with role-rotation hints written into the retry context.

When Rhea-class substrate is wired (a separate task in the eidos's docket once the rest of v1.0 lands), the substrate-dependent phases come online with no design changes to this ADR — ``eidos do`` becomes the orchestrator that calls Rhea rather than relying on the calling agent's substrate. The phase factoring, cardinality preflight, continuation envelope, and artifact contracts are all substrate-independent.

## Consequences

**For agents using eidos:**
- ``eidos do <task-id>`` becomes the primary work verb. Calling it kicks off the discipline; the agent (or substrate) responds to STUDY/RESEARCH/ADVERSARIAL/PLAN prompts; ``eidos do --continue <task-id>`` resumes after ACT.
- The CLI doesn't replace the agent's reasoning. It structures it. Where the agent would have just "done the task," it now runs through the discipline.
- Solo is the default. Most ``eidos do`` invocations complete without convening any cross-AI deliberation. Pod escalation happens only when one of the four triggers fires.

**For consumers of the eidos's artifacts:**
- Five durable artifacts per task. The repo accumulates real institutional knowledge: plans, praxis turns, completed-task records, SOR updates, plugin candidates.
- The system gets measurably smarter over time. Praxis pattern library grows; plugin candidates surface recurring problem shapes; governor accumulates the contracts the team has earned.

**For implementation:**
- New module ``eidos_cli/orchestrator/`` housing the eight-step discipline.
- New verb ``eidos do <task-id>`` with subcommands or flags for each phase (``--phase plan``, ``--continue``, etc.).
- The SOR routing SOP scaffold is created at eidos define time if governor is active.
- The plugin-candidate logging schema is created at eidos define time if praxis is active.
- New v1.0 task: integration tests for ``eidos do`` end-to-end against a fresh eidos.

**What this does NOT commit:**
- The Rhea / Pod-substrate integration. Real Pod deliberation lands when latency permits. ``eidos do`` is designed to plug Rhea in without restructuring.
- Auto-building plugins. ``eidos do`` only logs candidates. Promotion is a separate gated verb.
- Cross-eidos learning propagation. A task's learnings stay local to this eidos's praxis until a separate mechanism propagates them to peer/parent eidi.

## References

- [THE-EIDOS](../../../eidos-philosophy/THE-EIDOS.md) — what an eidos is
- [THE-LOOP](../../../eidos-philosophy/THE-LOOP.md) — the discipline this verb implements at scope level
- [THE-POD](../../../eidos-philosophy/THE-POD.md) — cardinality and escalation
- [THE-FORGE](../../../eidos-philosophy/THE-FORGE.md) — what each operational step produces
- [THE-ACCOUNTABILITY-CHAIN](../../../eidos-philosophy/THE-ACCOUNTABILITY-CHAIN.md) — verify against contracts
- [ADR-007](./ADR-007-eidos-as-unifying-agent-surface.md) — the structural commitment this verb operates over

## Implementation order (next session)

Phase-aligned with THE-LOOP's canonical names:

1. Scaffold ``eidos_cli/orchestrator/`` with one module per phase:
   ``perceive.py``, ``cardinality.py`` (preflight), ``decompose.py``, ``specialize.py``,
   ``act.py``, ``compress.py``, ``verify.py``, ``learn.py``, ``retry.py``.
2. Continuation envelope: ``eidos_cli/orchestrator/envelope.py`` — hash computation,
   verification on ``--continue``, stale-state refusal.
3. SOR routing SOP scaffold + parser (artifact-class keyed, not tag-keyed).
4. Plugin candidate schema + logging + per-eidos promotion threshold config.
5. High-stakes VERIFY fail-closed handler: when an operation is in the Solo-never-floor
   list and semantic verification is uncertain, emit a Pair-review or human-review
   prompt and pause execution.
6. Wire the verb ``eidos do <task-id>`` with phase invocation and ``--continue`` resumption.
7. End-to-end test against the eidos-cli-v1 eidos: run ``eidos do TASK-0004``
   (eidos spawn — itself a Solo-never-floor op, so VERIFY will exercise the fail-closed
   path), watch the discipline cycle, verify all five core artifacts produced + the
   continuation envelope correctly refuses a fabricated stale resume.
8. Iterate: tighten the per-phase prompts, surface gotchas during dogfood.
