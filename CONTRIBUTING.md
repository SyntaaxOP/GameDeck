# Contributing to GameDeck

GameDeck is intentionally a small local-first application. Please open an issue before a large feature so its privacy, failure modes, and V1 fit can be discussed first.

## Local workflow

1. Use Windows 10 or 11 with Python 3.12, Node.js 22, and pnpm 10 or newer.
2. Run `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`.
3. Create a focused branch and keep migrations with schema changes.
4. Run `.\scripts\verify.ps1` before submitting a pull request.
5. Describe user-visible behavior, tests, manual checks, and any recovery or privacy implications.

## Engineering expectations

- Keep process detection explicit: never track an executable the user did not register.
- Preserve UTC persistence, local calendar boundaries, and auditable session history.
- Keep external services optional; the core app must work offline without an account.
- Add deterministic tests for state transitions, failure behavior, and time boundaries.
- Never log unrelated process command lines or include local database/log files in commits.
- Prefer a migration and rollback-safe behavior over manual schema changes.

Generated UI primitives live in the repository and may be adapted. Keep accessible names, keyboard behavior, loading/error states, and responsive layouts intact.
