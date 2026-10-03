# Packaging and release checks

The distribution is `diffcontext-lab`, currently version 0.3.0. Its installed
commands are `diffcontext-lab`, `diffcontext-lab-mcp`, and the existing `diffcontext`
CLI alias. The import package remains `diffcontext` and can conflict with another
distribution using that name. Validate in an isolated environment.

**No public PyPI release has been performed.** No publisher account, publishing
credentials, or Trusted Publishing configuration is supplied by this repository.
Availability/ownership of the proposed PyPI name has not been established. Local
builds and CI artifacts do not imply public publication.

## Build and validate a wheel

From the repository root, using Python 3.10+ and pip 22.3+ (the checker uses pip's
`--python` option to install into its disposable environment):

```powershell
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/check_wheel.py dist/diffcontext_lab-0.3.0-py3-none-any.whl --typescript
```

The wheel checker creates a clean temporary environment, installs the wheel
with `[mcp,typescript]` when `--typescript` is supplied (otherwise `[mcp]`), and checks installed entry points, generated configuration,
and a real subprocess MCP connection away from the source checkout. It requires
network/package-index access to install dependencies. Inspect its result and exit
status before calling a wheel validated; merely building a wheel is insufficient.
See the script for the exact checks. Neither check changes user assistant settings
or calls a model provider.

Keep `pyproject.toml` and `diffcontext/__init__.py` versions synchronized before
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
python evals/coding_bench.py self-check
```

The environment variable makes a missing MCP SDK a failure instead of a skip.
The evaluation commands are development fixtures and model-free grading
calibration; their passing results are not evidence of real-agent improvements.
Use platform-appropriate environment-variable syntax outside PowerShell.

## Distribute before public publication

After committing and pushing, users with Git can install directly:

```powershell
python -m pip install "diffcontext-lab[mcp] @ git+https://github.com/Agamjot27/DiffContext.git"
```

That command follows the repository's current default branch. For a reproducible
installation, append `@<verified-commit-sha>` to the Git URL. Replace the placeholder
with an actual pushed commit; do not invent a release tag. A validated wheel can
also be shared as an artifact and installed with:

```powershell
python -m pip install "C:/path/to/diffcontext_lab-0.3.0-py3-none-any.whl[mcp]"
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
