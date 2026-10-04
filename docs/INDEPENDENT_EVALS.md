# Independent evaluation: the remaining data boundary

The four coding fixtures and seven retrieval cases are authored development
data. New tasks authored while looking at the implementation are still development
data. No independent held-out result has been collected.

## External benchmark candidate, not an implemented integration

SWE-bench provides real repository issue tasks with a Docker-based evaluation
environment. Its official [FAQ](https://www.swebench.com/SWE-bench/faq/) describes
the harness and dataset options. It requires a separate integration: our local
harness copies small Python fixtures and grades full-file edits; it does not yet
reproduce SWE-bench dependency environments, patch contracts or acceptance tests.
Do not run downloaded repositories through the trusted-fixture grader as if they
had its controlled execution boundary. No dataset or Docker images were downloaded.

## Protocol before collecting a headline metric

1. Have an independent selector freeze instance IDs, dataset revision, repository
   base commits and train/development/test assignment before inspecting gold fixes
   or tuning retrieval. Record why any instances were excluded.
2. Give the model only the issue/task and base-revision repository evidence. Keep
   gold patches, future commits, test patches and acceptance labels outside the
   index and prompt. Record context hashes and complete prompt/model settings.
3. Use executable acceptance outcomes in the benchmark's isolated environment.
   Patch-touched functions can be a localization proxy, but are not a complete
   definition of all code needed for a correct fix.
4. Pair policies at the same model/settings/budget and preserve provider errors,
   quota stops, attempts and unknown usage. Repeat samples and disclose task
   counts before presenting averages or statistical claims.
5. For memory, use corrections observed before a later task. Record timestamp,
   source revision, developer confirmation and freshness evidence. Synthetic
   advice written from the target gold fix cannot count as prior engineering memory.

The adapter in WI-013 prepares the provider boundary; it does not satisfy this
data/execution protocol by itself. Native Gemini/other adapters, external task
import, isolated grading and repeated-run analysis remain unimplemented.
