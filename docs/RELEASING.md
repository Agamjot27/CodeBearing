# Packaging and release checks

The distribution and import package are both `codebearing`, version 0.10.0.
Installed commands are `codebearing` and `codebearing-mcp`; new host entries use
`python -m codebearing.connect`. The old `diffcontext` Python namespace and legacy
console aliases are no longer shipped. See [migration notes](NAMING.md).

**No public PyPI release has been performed.** No publisher account, publishing
credentials, or Trusted Publishing configuration is supplied by this repository.
Availability/ownership of the proposed PyPI name has not been established. Local
builds and CI artifacts do not imply public publication.

0.9.0 validation on2026-10-05:188 source tests passed after the compiler repair;
clean wheel checks passed outside checkout with optional TypeScript/MCP, all six
tools, client configuration/setup and persistent cache reuse. The existing user's
tool was upgraded and its actual configured interpreter reported0.9.0. Existing
chats need reconnect. Details and wheel digest:
[WI-029](work-items/WI-029-codebearing-090-release/FEATURE.md).

0.10.0 namespace validation on 2026-10-06: 188 source tests passed and clean
wheel/TypeScript/MCP/setup/cache validation passed outside checkout. Only
`codebearing/` is shipped; existing user installations/configurations were not
upgraded automatically. [Migration record](work-items/WI-031-codebearing-namespace/FEATURE.md).

## Build and validate a wheel

From the repository root, using Python 3.10+ and pip 22.3+ (the checker uses pip's
`--python` option to install into its disposable environment):

```powershell
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/check_wheel.py dist/codebearing-0.10.0-py3-none-any.whl --typescript
```

Before a namespace migration build, remove only the verified generated `build/`
directory if it retains the old package. Setuptools can otherwise include stale
modules in a wheel. The checker explicitly rejects a `diffcontext/` namespace.
Do not delete source, user environments or data directories.

The wheel checker creates a clean temporary environment, installs the wheel
with `[mcp,typescript]` when `--typescript` is supplied (otherwise `[mcp]`), and checks installed entry points, generated configuration,
and a real subprocess MCP connection away from the source checkout. It also
checks opt-in cache persistence/reuse between the installed CLI and MCP process. It requires
network/package-index access to install dependencies. Inspect its result and exit
status before calling a wheel validated; merely building a wheel is insufficient.
See the script for the exact checks. Neither check changes user assistant settings
or calls a model provider.

Keep `pyproject.toml`, `codebearing/__init__.py` and the wheel-check filename in
`.github/workflows/checks.yml` synchronized before
building a later version; use that version's actual wheel filename. Build tools
and dependency installations may contact package indexes. Generated `dist/`,
build metadata, and temporary environments are local artifacts, not source.

## Test the source and transport

```powershell
python -m pip install -e ".[mcp,typescript]"
$env:DIFFCONTEXT_REQUIRE_MCP = '1'
$env:DIFFCONTEXT_REQUIRE_TYPESCRIPT = '1'
python -m unittest discover -s tests -v
python evals/run.py
python evals/investigate.py
python evals/typescript.py
python evals/indexing.py
python evals/coding_bench.py self-check
```

The environment variable makes a missing MCP SDK a failure instead of a skip.
The evaluation commands are development fixtures and model-free grading
calibration; their passing results are not evidence of real-agent improvements.
Use platform-appropriate environment-variable syntax outside PowerShell.

## Distribute before public publication

After committing and pushing, users with Git can install directly:

```powershell
python -m pip install "codebearing[mcp] @ git+https://github.com/Agamjot27/CodeBearing.git"
```

That command follows the repository's current default branch. For a reproducible
installation, append `@<verified-commit-sha>` to the Git URL. Replace the placeholder
with an actual pushed commit; do not invent a release tag. A validated wheel can
also be shared as an artifact and installed with:

```powershell
python -m pip install "C:/path/to/codebearing-0.10.0-py3-none-any.whl[mcp]"
```

The receiver still needs access to the wheel's dependency packages. Package users
then follow [assistant onboarding](MCP.md); they do not need an editable checkout.

## Public publication is a separate step

When a real publishing identity is available:

1. Verify project-name ownership/availability and agree the public release name.
2. Configure a publisher identity or repository-scoped Trusted Publishing. Keep
   credentials outside the repository and generated documentation.
3. Build the intended release revision, validate its wheel, run source checks,
   and inspect package metadata/content. Confirm the version is unused.
4. Publish through the configured release mechanism, then verify the downloaded
   public artifact in a clean environment.
5. Update onboarding with the actual verified package-index install command and
   record publication/verification in the work item and handover.

This guide does not upload packages, create a publishing workflow, claim a package
name, or claim a successful host connection. Each supported assistant still needs
its own integration smoke test; an SDK client transport check is narrower evidence.
