# Connect through MCP

DiffContext offers six read-only tools through a local stdio process. The host
chooses one repository when launching it; tool arguments cannot change that root.
No model or API key is needed to run the server or test its transport.

## Install the optional extra

From the project root, using Python 3.10+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[mcp]"
```

If virtual-environment creation fails during ensurepip but leaves an interpreter,
an existing pip installation can manage it with
`python -m pip --python .venv install -e ".[mcp]"`. The SDK is pinned to 2.3.0;
transitive dependencies are not locked. The core CLI still has no runtime dependencies.

## Demonstrate the connection

```powershell
.\.venv\Scripts\python.exe examples/mcp_client.py --repo examples/refunds
```

`examples/mcp_client.py:demonstrate()` launches a separate server, initializes an
SDK client, lists tools, searches, and compiles the first match. It prints the
result and closes the process. This proves transport, not coding-agent task success.

## Configure an MCP host

For a host accepting the common `mcpServers` JSON format, adapt these absolute paths:

```json
{
  "mcpServers": {
    "diffcontext": {
      "command": "C:\\Users\\Agamjot Singh\\Desktop\\DiffContext\\.venv\\Scripts\\python.exe",
      "args": ["-m", "diffcontext", "--repo", "C:\\path\\to\\your\\python-repository", "serve"]
    }
  }
}
```

Hosts may use a different configuration format. Use the same command and arguments
in that host's local stdio-server settings. Editable installation makes the module
available even when the host launches outside this project. No user host settings
are modified by this project. A Git revision request requires the actual Git root.
The server reserves stdout for MCP protocol messages; diagnostics go to stderr.

## Tool contracts

| Tool | Arguments | Result |
| --- | --- | --- |
| `search_symbols` | `query`, `limit=10` | Lexical matches with IDs and warnings |
| `localize_changes` | `ref="HEAD"` | Old/current changed seeds, removed symbols, unresolved changes |
| `analyze_impact` | `symbols` or `ref`, `depth=2` | Bounded callers/callees; separate versions for a ref |
| `compile_context` | `symbols` or `ref`, `max_tokens=4000`, `depth=2` | Cited text, eligible lessons, omissions and metadata |
| `get_lessons` | `symbols` | Confirmed fresh lessons for those current symbols; excluded metadata |
| `investigate` | `task` or `symbols` or `ref`, `max_tokens=4000`, `max_depth=3`, `max_steps=7`, `max_seconds=30` | Bounded gather/verify/expand loop, context and inline trace |

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

## Verification

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
