# Gemini CLI

This project is currently being managed by Gemini CLI.
Gemini acts as the primary builder, taking over from Codex and Claude.
The primary mission and engineering rules are defined in `AGENTS.md`.

## Workflow
- Operate on `gemini/*` branches.
- Keep `reports/PROJECT_STATUS.md` and `docs/risk-register.md` up to date.
- Validate mechanically using the provided CadQuery validation gates before exporting.
- Ensure all artifacts are reproducible via `make release`.
