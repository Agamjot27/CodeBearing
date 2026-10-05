# CodeBearing naming and 0.10.0 migration

The GitHub repository, distribution, CLI and Python source package are now named
CodeBearing / `codebearing`. The source directory is `codebearing/`, imports are
`from codebearing...`, and the MCP entry is `python -m codebearing.connect`.
`python -m codebearing` also supports public setup/help and advanced commands.

## Upgrading an installed 0.9.0 environment

Install the new Git revision in an isolated tool environment:

```shell
uv tool install --force --python 3.11 "codebearing[mcp,typescript] @ git+https://github.com/Agamjot27/CodeBearing.git"
```

Existing host configurations may still launch `-m diffcontext.connect`. Generate
new configuration from the interpreter that owns the new installation:

```shell
codebearing-mcp --repo "C:/path/to/your-project" --config codex
```

Use `claude` or `cursor` as needed. Replace only the existing CodeBearing entry
with this generated entry, preserving other servers. If using `setup`, it refuses
conflicting entries rather than silently overwriting them. Reconnect/restart the
assistant, then verify discovery with `--check`. Installation is separate from
host activation. This development change does not upgrade your existing global
tool or rewrite your BookMyShow configuration automatically.

## Why `.diffcontext/` still exists

The existing local SQLite data location is retained for compatibility, so confirmed
lessons and indexing cache are not silently abandoned. It is an on-disk format
name, not the import package. Do not rename it manually. A data-directory change
needs an explicit migration with rollback and mixed-version behavior first.
Historical work-item records and published trial hashes retain their original
names; changing them would rewrite evidence rather than rename current code.

## Renaming the checkout folder

Fresh clones use `CodeBearing` by default. The active desktop checkout may still
be called `DiffContext`; its basename has no effect on package imports.
To rename that open workspace, finish/close sessions and terminals using it,
then run from its parent directory:

```powershell
Rename-Item -LiteralPath "C:/Users/Agamjot Singh/Desktop/DiffContext" -NewName "CodeBearing"
```

Verify no separate `CodeBearing` directory already exists first. Reopen the new
folder in your editor/Codex project and recreate local virtual environments if
needed: Windows virtual environments can embed absolute paths. Regenerate host
entries if they reference an interpreter or repository under the renamed folder.
This session keeps its registered workspace root intact to remain usable.
