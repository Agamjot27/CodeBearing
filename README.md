# CodeBearing

**Give your coding assistant the right code—and lessons from past corrections.**

CodeBearing is a local MCP server for Claude Code, Cursor and Codex. When you ask
your assistant to change something, it finds relevant functions, follows their
dependencies and returns a compact context package. Confirmed lessons can warn
the assistant about mistakes you previously corrected.

Your assistant makes the edits. CodeBearing supplies the evidence.

## Start using it

With [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git installed:

```powershell
uv tool install --python 3.11 "codebearing[mcp,typescript] @ git+https://github.com/Agamjot27/DiffContext.git"
```

From the project you want to work on, connect your assistant:

```powershell
codebearing setup --client cursor
```

Use `--client claude` or `--client codex` instead. Setup adds CodeBearing to that
project's settings, preserves other servers, and verifies all six tools. Open/
restart your assistant in the project and approve or enable CodeBearing when
prompted. You don't need to run the server yourself.

Then ask:

> Use CodeBearing to investigate this bug before editing. Explain the relevant
> functions, their dependencies and any applicable lessons. Make the fix and run tests.

No separate model API key is needed for CodeBearing. Your assistant uses its own
account. Python and JavaScript/TypeScript are supported, with static-analysis
limits. The install command includes both language adapters.

**Install status:** CodeBearing 0.6.1 is installable from this Git repository.
It has not been published to PyPI; don't use `pip install codebearing` yet.
The repository URL still uses its earlier DiffContext name.

## What it gives your assistant

- Relevant source excerpts, file locations and explanations for inclusion.
- Callers and dependencies within an explicit depth and text budget.
- Tracked Git-change context, including deleted code.
- Developer-confirmed lessons, excluding stale evidence.
- Visible omissions, warnings and a trace of the investigation.

It does not edit your code or prove a fix is correct. Your assistant should inspect
the evidence and run your project's tests. We haven't measured independent
real-world coding improvement yet.

## More help

- [Setup and troubleshooting](docs/MCP.md)
- [First bug-fix walkthrough](docs/FIRST_TASK.md)
- [Language support](docs/LANGUAGES.md)
- [Advanced development and evaluation commands](docs/DEVELOPMENT.md)
- [Engineering decisions](DECISIONS.md) and [execution flows](FLOW.md)

The evaluator and OpenRouter adapter are developer tooling. You do not need them
to use CodeBearing in your coding assistant.
