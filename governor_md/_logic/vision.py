"""Vision: view, set.

**DEPRECATED.** Per ADR-007 in this repo, the Telos forge in eidos-cli is
the canonical owner of the project's destination artifact (statement plus
the three ``_when`` trigger fields). Governor's ``vision-set`` and
``vision-view`` remain available for backward compatibility but emit a
deprecation notice. The four-field telos contract belongs to telos-md /
eidos.

Migration path for existing consumers:

  1. Run ``eidos define <repo>`` (or migrate-in-place via ``eidos migrate``)
     to create an eidos at the repo with a proper four-field telos artifact.
  2. Use ``eidos telos view`` / ``eidos telos supersede`` instead of
     ``governor vision-view`` / ``governor vision-set`` going forward.
  3. governor-md continues to own contracts (goals, guardrails, SOPs, ADRs)
     — these stay first-class.

The hard removal of vision-set/vision-view will land in a future major
version bump of governor-md once consumers have migrated.
"""

from __future__ import annotations

import sys

from ._session import resolve


_DEPRECATION_NOTICE = (
    "[deprecated] governor.vision is deprecated — the four-field telos contract "
    "now lives in the Telos forge (eidos-cli). Use `eidos telos view` and "
    "`eidos telos supersede` going forward. See ADR-007 in governor.md/.governor/adr/."
)


def vision_view(project_id: str | None = None) -> str:
    """View the project vision. **Deprecated — use ``eidos telos view``.**"""
    print(_DEPRECATION_NOTICE, file=sys.stderr)
    core = resolve(project_id)
    vision = core.get_vision()
    if not vision:
        return "No vision document found."
    return f"# {vision.title}\n\n{vision.body}"


def vision_set(title: str, body: str, project_id: str | None = None) -> str:
    """Set or update the project vision document. **Deprecated — use ``eidos telos supersede``.**"""
    print(_DEPRECATION_NOTICE, file=sys.stderr)
    core = resolve(project_id)
    core.set_vision(title, body)
    return f"Vision updated: {title}"
