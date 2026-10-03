# WI-014 — CodeBearing name and install/connect experience

Status: implementation complete; actual assistant trial pending
Opened: 2026-10-04

## User request / scope

User selected CodeBearing and wants the existing product easy to install and
connect, instead of more evaluation infrastructure. Starting at 21d30db, package
and commands still use diffcontext-lab and users copy configuration manually.
Rename public distribution/commands/server/config identity; preserve legacy
commands and existing internal storage. Add project-scoped setup with verified
MCP connection, safe merge and plain next steps. Simplify README and start guide.
Validate a clean release wheel and a real transport; do not claim a real coding
assistant outcome from SDK tests. Public PyPI identity is not configured.

## Plan / execution

pyproject.toml entry → onboarding.py:main() setup → connect.check_connection()
→ safe project configuration merge → assistant launches connect.main() → six tools.
Codex/Claude/Cursor project formats checked against official docs. D-023/F-033
will explain the implementation choices and actual paths.

## Attempts / verification

Implemented the name, safe project setup, concise main guide and first-task guide.
Six onboarding tests cover preserving settings, idempotence, malformed/conflicting
settings, concurrent changes, symlinks and failed transport before writes.
Full suite: 155 passing tests. After checking official Cursor docs, added explicit
stdio type for both JSON clients; seven connection tests then passed.
Rebuilt 0.6.0 wheel; fresh-environment validation passed install, CLI/hybrid task,
project setup, configuration, six-tool stdio discovery/search and cache reuse.
A broad guide rename temporarily changed the GitHub URL; corrected it before release.
Installed the clean wheel as an isolated uv user tool; codebearing --help and
codebearing-mcp --check verified the installed six-tool transport. uv's managed
Python 3.11 download failed with a missing target directory; using the existing
Python 3.13 interpreter succeeded. No tool settings were written to a real project.
Review caught an incorrect practice-example description; changed it to the actual
refund-rounding fixture and documented its correct per-line expected behavior.
No PyPI ownership/publication or actual host coding outcome is claimed.
Model/provider trials are paused in favor of product polish.

## Handoff / Git trace

Use git log --oneline -- docs/work-items/WI-014-codebearing-onboarding/FEATURE.md.
