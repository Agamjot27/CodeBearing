# Persistent incremental indexing

Enable caching once in your assistant's generated configuration:

```powershell
diffcontext-lab-mcp --repo "C:/path/to/project" --cache --config claude
```

Use `cursor` or `codex` in place of `claude` for those clients. Merge the generated
configuration as described in [MCP setup](MCP.md). The printed arguments retain
`--cache`; generation itself does not create a database. The server remains the
same six-tool MCP server. Tools read source and lessons; this option writes only
disposable derived index state.

For the CLI:

```powershell
python -m diffcontext --repo examples/refunds --cache index
python -m diffcontext --repo examples/refunds --cache compile --symbol billing.py:refund_total
```

The first request captures and parses files, then saves functions, call facts and
the resolved graph in `.diffcontext/index.sqlite3`. Repeated requests read current
source bytes and compare SHA-256 fingerprints. Unchanged parse facts are reused;
changed or new files are parsed, and deleted files disappear. The whole current
graph is linked again so changed imports/exports cannot leave obsolete edges.
Warm requests do not rewrite the unchanged cache generation. This works across
process restarts, for Python and the optional TypeScript/JavaScript adapter.

`indexing` metadata reports captured, parsed, reused, removed and uncached files.
`elapsed_ms` covers cache lookup/parsing/linking/publication after capture;
ordinary current-file builds also report `capture_ms` and `total_ms`. Git-based
requests report only the cached tracked-current build; historical Git blobs still
parse afresh and Git/blob-read costs are outside these cache counters. Investigation
reports and their summaries preserve the counters. No file watcher or mtime shortcut
is used. Capturing a changing working tree is still not atomic.

Parser/runtime/package or schema/root changes invalidate incompatible facts.
Checksums detect accidental payload damage; malformed facts reparse. Corrupt or
unwritable cache storage returns fresh evidence with a warning. The cache is not
an integrity/security boundary against deliberate local tampering. It contains
source excerpts, is local, and is ignored by Git. Add `.diffcontext/` to your own
repository's ignore rules. Engineering lessons remain in the separate
`memory.sqlite3`; clearing derived index state must preserve that file. Caching is
opt-in; without `--cache`, retrieval does not create repository-local state.

SQLite tables: `metadata` (schema/root), `files` (fingerprints and JSON parse facts),
`symbols` (current symbol descriptions), `edges` (current resolved calls).
Publication is transactional. No Neo4j/server, worker, target-code execution,
provider calls or skill/plugin framework is introduced.

## Measurement

`python evals/indexing.py` compares full, empty-cache, warm-cache and one-file-edit
requests. It checks exact graph/output parity and parse counts. Timing is reported,
not a fixed CI threshold. The workload is 120 authored Python files/960 functions,
three repetitions, with separate warmup and alternating paired order. Operating
system caches are not flushed; an empty index cache is not a cold machine.

The saved [local run](work-items/WI-008-incremental-indexing/indexing-local.json)
reported median full/warm times of 105.255/30.950 ms, empty-cache initialization
276.860 ms, and full/cached single-edit times of 99.242/69.762 ms. Warm requests
parsed zero files; an edit parsed one and reused 119. These are local fixture
measurements, not production scale, coding-success or competitor comparisons.
All files are still read, all relationships relinked, and changed generations
rewrite derived tables; large repositories may require more selective storage.

Implementation: D-018, F-028 and WI-008. Hybrid retrieval and live coding evaluations
remain the next phases.
