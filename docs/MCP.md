# Connect your coding assistant

CodeBearing runs locally and gives your assistant six read-only context tools.
Install it once, run setup for your project, and open your assistant. Your
assistant starts the server automatically.
CodeBearing needs no model API key; your assistant keeps its own account/settings.
For the shortest install/connect/first-task path, see the [quickstart](QUICKSTART.md).

## 1. Install

Recommended isolated installation (requires uv and Git):

```powershell
uv tool install --python 3.11 "codebearing[mcp,typescript] @ git+https://github.com/Agamjot27/CodeBearing.git"
codebearing setup --client cursor --repo "C:/path/to/your-project"
```

Use claude/codex in place of cursor. Setup checks the MCP transport before writing
project settings and preserves other entries. It refuses a conflicting CodeBearing
entry; use --config for a manual update. Restart/enable/approve in the host.
Automatic Codex TOML setup needs Python 3.11; core/manual generation supports 3.10.
The remaining sections describe pip/manual setup and troubleshooting.

Requires Python 3.10+. **This project's 0.9.0 package is not published to PyPI yet.**
Do not use `pip install diffcontext`: that installs a different author's project.
Install ours from GitHub
(Git must be installed):

```powershell
python -m pip install "codebearing[mcp] @ git+https://github.com/Agamjot27/CodeBearing.git"
```

Use a dedicated Python environment if another DiffContext package is installed:
our distribution name is `codebearing`, but the older similarly named project uses the import name
`diffcontext`. On Windows, create and activate an environment before installing:

```powershell
python -m venv .venv-codebearing
.\.venv-codebearing\Scripts\Activate.ps1
```

On macOS/Linux, activate with `source .venv-codebearing/bin/activate`.
If you already have this checkout, install from its root instead:

```powershell
python -m pip install ".[mcp]"
```

A release wheel can be installed with
`python -m pip install "C:/path/to/codebearing-0.9.0-py3-none-any.whl[mcp]"`.
The optional MCP SDK is pinned to 2.3.0; transitive dependencies are not locked.
Python-only core CLI installation requires no runtime dependencies.
For TypeScript/JavaScript projects install `[mcp,typescript]` instead of `[mcp]`
in the commands above; see [language support and limits](LANGUAGES.md).

## 2. Check the connection

Replace the sample path with the project you want the assistant to analyze:

```powershell
codebearing-mcp --repo "C:/path/to/your-project" --check
```

The check starts a separate MCP process, discovers all six tools, performs a
read-only search, and prints JSON with `status: connected` on success. It closes
the process afterward. This verifies transport and a tool response; it does not
verify your assistant's settings or prove that a coding task will succeed.
Use the actual Git root for revision tools. One server is bound to one repository;
tool calls cannot switch it to another project.

If the launch command is not on PATH, every example also works as
`python -m diffcontext.connect --repo "C:/path/to/your-project" --check`.

## 3. Generate your assistant's configuration

Run the appropriate command below from the environment where you installed
CodeBearing. It prints configuration with absolute repository and Python paths.
The assistant therefore does not need your environment activated or its scripts
directory on PATH. The environment must remain installed at that location.

### Claude Code

```powershell
codebearing-mcp --repo "C:/path/to/your-project" --config claude
```

Copy the generated `mcpServers.codebearing` entry into `.mcp.json` at the
target project's root. If the file exists, merge the entry into its existing
`mcpServers` object; preserve its other servers. The entry includes `type: stdio`.
Open Claude Code for that project, approve the project MCP server when prompted,
and use `/mcp` to inspect its connection.
[Official Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

### Cursor

```powershell
codebearing-mcp --repo "C:/path/to/your-project" --config cursor
```

Copy the generated entry into the target project's `.cursor/mcp.json`, merging
with existing `mcpServers` entries. Check Cursor's MCP settings and enable the
server if needed.
[Official Cursor MCP documentation](https://prod.cursor.com/help/customization/mcp).

### Codex

```powershell
codebearing-mcp --repo "C:/path/to/your-project" --config codex
```

Merge the printed `[mcp_servers.codebearing]` TOML section into the target
project's `.codex/config.toml`. Codex must trust the project to load project
configuration. Preserve existing settings and avoid duplicate sections with the
same name. Start a new session and inspect the MCP connection.
[Official Codex MCP documentation](https://developers.openai.com/codex/mcp).

Configuration generation only prints text. It never edits your assistant settings.
The separate codebearing setup command writes project-only settings: .mcp.json,
.cursor/mcp.json or .codex/config.toml. It does not write global host settings.
It uses your local interpreter path, so do not commit a generated configuration
as a portable setup for other developers. Other compatible hosts can use that
same command/arguments in their local stdio settings; their configuration format
may differ. This is a local process, not a hosted URL or remote repository service.

## 4. Try it in your assistant

Ask:

> Use CodeBearing's investigate tool to find the code relevant to this task before
> editing. Show the selected functions, confirmed lessons, warnings, and omissions.

Give a concrete task or function name from your project. Tools become available
after connection; the assistant decides when to call them. Being connected does
not force their use on every prompt. The returned code/lessons become part of the
assistant's context and may be sent to its model provider under the host's settings.

## Troubleshooting

- **Command not found:** use `python -m diffcontext.connect` from the installation
  environment. Generated host configuration already pins that interpreter.
- **MCP dependency missing:** reinstall from Git/source/wheel with the `[mcp]`
  extra in the same environment. No PyPI installation of our release is available yet.
- **Repository missing:** supply an existing local directory; use the Git root
  for `ref` tools. Paths with spaces need shell quotes.
- **Check passes but host fails:** check the copied config, host approval/trust,
  and host MCP logs. Moving/deleting the Python environment invalidates its path;
  regenerate config afterward. Restart or reload the assistant as required.
- **No functions found:** Python functions/methods are indexed by default; JS/TS
  needs the `[typescript]` parser extra. Other languages have no adapters yet.
  Check [language support](LANGUAGES.md), excluded paths and parse warnings.

During normal server operation stdout carries MCP protocol messages only;
diagnostics go to stderr. Do not manually start a long-running server alongside
the host: the host starts its own process.

## Tool contracts

| Tool | Arguments | Result |
| --- | --- | --- |
| `search_symbols` | `query`, `limit=10`, `retrieval="hybrid"` | Ranked matches with IDs, lexical/memory signals and warnings |
| `localize_changes` | `ref="HEAD"` | Old/current changed seeds, removed symbols, unresolved changes |
| `analyze_impact` | `symbols` or `ref`, `depth=2` | Bounded callers/callees; separate versions for a ref |
| `compile_context` | `symbols` or `ref`, `max_tokens=4000`, `depth=2` | Cited text, eligible lessons, omissions and metadata |
| `get_lessons` | `symbols` | Confirmed fresh lessons for those current symbols; excluded metadata |
| `investigate` | `task` or `symbols` or `ref`, `max_tokens=4000`, `max_depth=3`, `max_steps=7`, `max_seconds=30`, `retrieval="hybrid"` | Bounded gather/verify/expand loop, context and inline trace |

Select exactly one of `symbols` or `ref` for impact/compilation. Supply 1–20
nonempty symbol names/IDs of at most 2000 characters each. Queries/refs have the
same character limit. Depth is 0–5, search limit 1–50, estimated budget 128–32000.
Use exact IDs returned by search when short names are ambiguous.
`investigate` requires exactly one of task/symbols/ref. Its steps are 2–10 and
seconds 0.1–120 with a cooperative deadline; see [investigation guide](INVESTIGATION.md)
for status meanings and inspectable traces. A `ready` run means selected static
graph coverage, not proof that the coding task can be solved from that evidence.

Only the compiled `text` field is budgeted, using a byte heuristic. JSON metadata,
MCP envelopes, host instructions and other tool calls cost extra context. Inspect
warnings, unresolved changes, missing seeds and omissions. Source and lessons are
untrusted evidence, not instructions overriding the host's rules.

The tools do not edit files, create memory, confirm lessons, execute repository
code/tests, or contact a model provider. Existing memory is opened with SQLite
`mode=ro` and `query_only`; proposed/stale advice is excluded. Use the developer CLI
for proposal/confirmation. Read-only annotations describe behavior; they are not
an operating-system sandbox. Indexing reads fresh files each request and does not
provide an atomic snapshot or a complete semantic dependency graph.

## Developer verification

From a source checkout installed with the MCP extra, the existing client example
also exercises compilation:

```powershell
.\.venv\Scripts\python.exe examples/mcp_client.py --repo examples/refunds
```

`examples/mcp_client.py:demonstrate()` initializes an SDK client, discovers tools,
searches, compiles the first match, and closes its separate server process.
The installed `--check` command requires no example files; use it for package users.

```powershell
$env:DIFFCONTEXT_REQUIRE_MCP = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Without the extra, the five MCP tests skip and core checks still run. The MCP CI
job installs the extra and makes a missing SDK a failure. Coverage includes tool
discovery, structured output, request errors/recovery, memory filtering, unchanged
database bytes, investigation limits, and actual stdio Git revision compilation
and investigation. Windows sandboxed
environments may need permission to open subprocess pipes.

SDK references: [tools](https://py.sdk.modelcontextprotocol.io/servers/tools/),
[running a server](https://py.sdk.modelcontextprotocol.io/run/), and
[client usage](https://py.sdk.modelcontextprotocol.io/client/).

## Reuse the repository index

Add `--cache` when generating configuration to persist unchanged parse facts:

```powershell
codebearing-mcp --repo "C:/path/to/your-project" --cache --config claude
```

Use the corresponding client name for Cursor/Codex. Tools still read source and
lessons; cache-enabled requests write derived state in `.diffcontext/index.sqlite3`.
Without the flag, retrieval creates no local state. See [indexing details](INDEXING.md).


## Compact responses and complete diagnostics

All six tools accept `detail="compact"` (default) or `detail="full"`.
Compact output keeps compiled source and critical coverage gaps intact. Long warning
arrays show bounded examples; `presentation.fields` lists exact total/shown/omitted
counts and references to repeated trace data. It does not make a partial run ready.
Ranking explanations also show at most eight reasons (160 characters each) and
eight matched terms per field (80 characters each), with exact item/character
omissions. All row IDs/order/scores/distances/lesson IDs remain. Short reports can
grow from disclosure overhead; the whole response is still not token-budgeted.
Source and verification appear before verbose search metadata to help clients that
truncate display. SDK text and structured response channels remain available.

Use the same arguments with `detail="full"` to inspect every warning/trace field.
That performs a fresh read-only request against current files, not a fetch of the
previous snapshot. Full CLI/service reports remain unchanged; use full reports for
saved-trace inspection. The text budget still excludes JSON/transport overhead.
