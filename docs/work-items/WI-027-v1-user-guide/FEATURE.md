# WI-027 — A clear first-use path and reproducible demonstration

Status: complete
Opened / updated: 2026-10-05

## Request and scope

Finish the user-facing presentation while implementation/evaluation proceeds in
parallel. Provide one concise install/connect/first-task guide, a reproducible demo
storyboard, and an honest roadmap. No frontend, hosting, global configuration,
private project edits, fabricated recordings or unmeasured performance claims.

## Starting state and execution path

README already contains Git-based isolated installation and project setup, but
advanced documents are the only troubleshooting path. ROADMAP has outdated claims
that no real assistant sessions have run and treats demonstrated integration as
future work. Public Luna evidence is one authored task, with process interruptions
and no per-run token telemetry.

Existing execution: `diffcontext/onboarding.py:main()` → `prepare_config()` →
`diffcontext/connect.py:check_connection()` → local stdio MCP discovery/search →
`save_config()` publishes project configuration → assistant invokes
`diffcontext/mcp_server.py:create_server()` registered tools →
`diffcontext/service.py:RepositoryService.investigate()` → compiled evidence.
Relevant flows: F-033, F-037, F-039/F-040. Function names checked against source.
No execution flow changed.

## Implementation and decisions

Added docs/QUICKSTART.md, docs/DEMO.md, README links and ROADMAP current-state
corrections. Kept the user path separate from developer evaluation commands. Used
an authored public fixture so demonstrations can be reproduced without private
source, credentials or paid API calls. Present observed metrics with their unit
and scope; newly collected results remain pending until verified by the parent.

## Attempts and outcomes — update during work

- Read session continuity, README, MCP, FIRST_TASK, LANGUAGES, Luna trial,
  ROADMAP, relevant decisions and flows. Found a stale distribution name in
  LANGUAGES and a Python-only troubleshooting statement in MCP; these are outside
  this worker's initial ownership; parent then authorized correcting both.
- Corrected LANGUAGES' Git installation distribution/repository and MCP's
  Python-only troubleshooting statement; added a quickstart link to MCP.
- Added the install/connect/task path with exact existing setup options; explained
  that the assistant starts the MCP process and must actually call a tool.
- Added a public refund fixture recording storyboard, existing test blind spot,
  exact bug prompt, artifact capture steps and scoped metric links. No video made.
- Updated stale roadmap claims about actual assistant use/live outcomes and
  clarified implemented confirmed memory versus future automatic capture.
- Follow-up: read the verified memory continuity report and linked it from README
  and DEMO. Explained authored reproduction/observed historical provenance,
  explicit operator review, fresh interpreter and no later-model efficacy claim.
  Broader CLI-pilot metrics remain excluded pending the verified paired report.
- First inline link-check command failed PowerShell parsing because of nested
  quotes; replaced it with a single Python script piped from a literal here-string.
  Running onboarding as a module printed no help because that module has no
  execution guard; called its actual `main(['setup', '--help'])` instead.

## Verification

- Python link checker: 30 relative Markdown targets checked, none missing, across
  README/QUICKSTART/DEMO/ROADMAP/MCP/LANGUAGES. External pages were not fetched; they are existing
  installation references, not new product recommendations or claims.
- `.venv/Scripts/python.exe -c "from diffcontext.onboarding import main; ..."`
  verified `setup --help` accepts three named clients, repo and cache arguments.
- `.venv/Scripts/python.exe -m unittest discover -s
  evals/coding_tasks/refund-rounding/repo -v`: both public checks pass.
- Imported fixture `refund_total(['0.005', '0.005'])`: observed `0.01`, confirming
  the documented baseline symptom while public tests pass.
- Source searches confirm named setup/connect/server/investigation functions.
- `git diff --check` passed (Git emitted normal Windows line-ending warnings).
  Documentation does not establish installation on every host, a recorded video,
  real-world general benefit or any model-token/cost savings.

## Handoff / completion

Parent owns root HANDOVER/DECISIONS/FLOW and final release/version updates. Existing
D-023 installation/product scope and D-026/D-028 controlled comparisons remain
applicable; no architecture changed. The rationale is to make existing MCP use
clear before adding UI/infrastructure and make every public metric traceable.
New broader trial links can be added once the evaluation owner verifies their
evidence. Current docs explicitly label pending work and static limits.
The verified memory report is linked. Parent added the completed32-call report,
its negative comparative outcome and separately labeled8-call retry verification
to README/DEMO/ROADMAP. D-035/F-045 record why current MCP onboarding precedes UI.
Native recording remains unavailable; no video was fabricated.
Final parent link check:38 local targets present across public entry guides and
measured/memory reports. Added narrow Python exception-evidence support/limits to
LANGUAGES after the separately tested WI-028 implementation.

## Git trace

Find the introducing commit with
`git log --oneline -- docs/work-items/WI-027-v1-user-guide/FEATURE.md`.
