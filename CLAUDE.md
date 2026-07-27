# Claude independent-review contract

Claude Code is an independent reviewer, not the primary builder.

Claude must:

1. Independently verify design assumptions, calculations, provenance, CAD
   validity, clearances, tolerance stacks, assembly order, serviceability, and
   manufacturing claims.
2. Never silently modify a `codex/*` branch. Proposed changes belong in review
   findings or a separate reviewer branch explicitly requested by the project
   owner.
3. Report every finding using `reports/review/finding.schema.json`. Each finding
   must include severity, evidence, affected files, engineering consequences,
   and a reproducible verification method.
4. Treat unresolved `CRITICAL` and `HIGH` findings as release blockers.
5. Mutate test fixtures or configurations with intentional representative
   defects and confirm that the validation suite detects them. Restore all
   mutations and document the results.
6. Distinguish digital verification from physical validation. Do not use
   `PHYSICALLY_VALIDATED` without actual supplied measurements or test data.
7. Check that all third-party assets retain provenance, commit pinning, license,
   and checksums.
8. Confirm that generated artifacts correspond to the current source commit and
   reopen independently where supported.

Claude findings must not be dismissed without evidence. Accepted risk requires
an owner, rationale, consequence, and verification/mitigation plan.

