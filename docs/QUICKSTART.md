# Use CodeBearing in your coding assistant

CodeBearing is a local MCP server: your assistant asks it for relevant code and
confirmed lessons, then makes and tests the changes itself. There is no separate
dashboard, model account or server to keep running manually.

## Install once

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then
run this in a terminal:

```powershell
uv tool install --python 3.11 "codebearing[mcp,typescript] @ git+https://github.com/Agamjot27/CodeBearing.git"
```

This includes Python and JavaScript/TypeScript indexing. CodeBearing is available
from Git; the package has not been published to PyPI yet.

## Connect a project

Open a terminal **in the project you want to work on**, then choose your assistant:

| Assistant | Run once for this project |
| --- | --- |
| Claude Code | `codebearing setup --client claude` |
| Cursor | `codebearing setup --client cursor` |
| Codex | `codebearing setup --client codex` |

Setup checks the six MCP tools and adds project settings while preserving other
servers. Open or restart your assistant in that project and enable/approve
CodeBearing. Codex must trust the project to load its project configuration.
The assistant starts CodeBearing automatically. Repeat setup in each new project.

## Give it a real task

Replace the bracketed text with a concrete symptom and expected result:

> Use CodeBearing's investigate tool before editing. The bug is: [what happens].
> Expected behavior: [what should happen]. Show the relevant functions,
> dependencies, confirmed lessons and missing evidence. Fix the bug and run tests.

Check that the assistant's tool activity actually calls `investigate` on
CodeBearing. A connection alone does not force the assistant to use it.

You should see cited functions/source, applicable confirmed lessons if any,
coverage warnings or omissions, and an investigation trace. `partial` means some
evidence is missing; ask the assistant to inspect those gaps. If it finds the wrong
function, ask it to use `search_symbols` and investigate the exact returned ID.
An empty lesson list is normal until you have saved and confirmed a correction.

Review the assistant's diff and test results as usual. CodeBearing's evidence
does not prove that its fix works.

## If it does not appear

From the same project, run:

```powershell
codebearing-mcp --repo . --check
```

`status: connected` verifies the local MCP process, not the assistant's approval
or configuration loading. If the check succeeds, reopen the project/start a fresh
chat, confirm trust/approval and inspect the host's MCP settings/logs. If setup
reports a conflicting existing entry, follow the manual configuration instructions
instead of deleting other servers. See [setup troubleshooting](MCP.md).

CodeBearing performs static analysis of Python and optional JS/TS. Dynamic calls,
framework wiring and unsupported languages can be missing. Repository evidence
returned to the assistant may be sent to its model provider under that assistant's
settings. CodeBearing itself makes no model-provider call.

Try the [public demo walkthrough](DEMO.md), or see [language limits](LANGUAGES.md).
