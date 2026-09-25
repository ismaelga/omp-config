# Traps

Each one cost a pass to find. Symptom → cause → how it was detected.

## Identity and routing

**Same model, two spellings, two bills.** `anthropic/claude-fable-5.1` (dot) is
OpenRouter's id; the `anthropic` provider spells it `claude-fable-5-1` (dash). The dot
form silently resolves to the metered OpenRouter route instead of the subscription
route. → Resolve the selector and read which provider answered; never assume the
spelling carries across providers.

**Vendor reroutes an id to different weights.** DeepSeek retired `deepseek-v4-flash` and
routed it to V4.1-Flash; from 2026-09-14 `deepseek-v4-pro` follows. A pin that still
names the old id keeps working while serving something else. → Read the vendor's
deprecation notice, not just the price page.

**Provider requires a client version.** Anthropic 400s `claude-fable-5-1` below claude-cli
2.1.257 (docs) / 2.1.251 (observed). The version travels in a billing line injected as
`system[0]` (`x-anthropic-billing-header: cc_version=…`), not an HTTP header, so a
User-Agent audit looks fine while every request fails. → Read the 400 body.

**Region gate looks like a broken chain — and gates lift.** opencode-go's DeepSeek ids
were China-only and answered HTTP 403 ("requires explicit opt in") on 2026-09-01, so an
`opencode-go/*` wildcard dead-ended for any DeepSeek head. On 2026-09-11
`opencode-go/deepseek-v4.1-flash` answered `OK` through the session path: DeepSeek's
V4.1-Flash announcement names OpenCode an official partner. A gate is a dated
observation, not a property. → Re-probe every gated route each pass, not just the ones
you expect to have changed.

**Retired hop still in the catalog.** `ollama-cloud/gemini-3-flash-preview` answers HTTP
410 "retired at 2026-07-15" and sat as hop 2 of the vision chain for months while
remaining listed in the bundled catalog. → Link audit; the catalog does not prove
liveness.

**Invite-only model in the catalog.** `claude-mythos-5-1` is the same weights as Fable
5.1 behind an invite program. It appears in the provider catalog and is unreachable. →
Vendor docs.

## Prices

**A `:batch` row is not a discount.** OpenRouter lists `model:batch` at ~50% — that is
the batch API. Interactive price is the plain row. Reading the batch row as a live
discount produced a wrong rationale for the `vision` pin.

**A promo price is a promo.** Gemini 3.7/3.8 Flash `$0.75/$3.75` is Google's
introductory price through 2026-12-31, then `$1.50/$7.50`. OpenRouter's genuine 50%
discount on 3.7-flash (`$0.375/$1.875`, verified 2026-08-28) had ended by 2026-09-10. →
Re-check every price a pin's rationale rests on, and write the exit condition into the
comment.

**Catalog prices go stale.** Luna/Terra carried pre-2026-07-30 launch prices long after
the cut. → `models.yml` `modelOverrides` corrects them; verify against the vendor
announcement.

**Peak/off-peak pricing.** DeepSeek's published rates double at peak. A single quoted
number hides a 2× swing.

## Context windows

**Three different ceilings per model.** `gpt-6-astra`: 272,000 is the backend *default*,
872,000 the plan ceiling (codex clamps user overrides to `max_context_window`), and
1,050,000 the API tier reachable only with an `OPENAI_API_KEY`. The bundled catalog
pinned the default, so the harness compacted at a third of what the plan allowed. →
`~/.codex/models_cache.json` for plan-side truth; models.dev reports the API tier.

**An output cap on a brand-new discovery row is a guess.** `ollama-cloud/deepseek-v4.1-flash`
landed in the catalog with `maxTokens: 8192` while every sibling DeepSeek row on that
provider carries 65,536 (`isOllamaCloudOutputCapped` pins them to
`min(contextWindow, 65536)`) and the vendor advertises 384K. One wire call settled it:
"count from 1 to 4000, one per line" returned all 4000 lines, 11,469 tokens,
`done_reason: "stop"` (2026-09-11). The row is corrected in `models.yml`. Cloud rows
also carry `omitMaxOutputTokens: true`, so a wrong cap skews budgeting rather than
truncating the wire — which is why it survives unnoticed. → Ask a new row for more
output than its cap claims before trusting it.

## Effort tiers

**Bare selector means `auto`, and `auto` can reach the top.** With
`providers.autoThinkingMaxEffort: max`, an unpinned reasoning role can be classified
into `max`, and the top tier reliably buys latency rather than correctness. Opus 5 on
Artificial Analysis v4.3 (read 2026-09-10): max 51 / xhigh 50 / high 48, at first-chunk
latencies of 94.9 s / 30.6 s / 26.0 s — one index point for three times the wait. GPT-6
Astra on the same table: medium 50 at 5.8 s against max 53 at 334.8 s.

**`:low` is not uniform.** ollama-cloud GLM rows serve a ladder starting at `high`;
`:low`/`:minimal` clamp up to `high` (`clampThinkingLevelForModel` falls back to
`levels[0]`). zai and openrouter/z-ai do serve `low`. Two selectors that look like the
same request are not.

**An Ollama Cloud effort ladder is stamped, not served — and the harness hides it.**
Discovery sets `[minimal, low, medium, high]` for any row whose `/api/show`
capabilities include `thinking` (`ollamaCloudModelManagerOptions`), regardless of what
the backend accepts. `ollama-cloud/deepseek-v4.1-flash` carries exactly that ladder
while a raw POST of `"think": "minimal"` to `ollama.com/api/chat` answers
`400 invalid think value: "minimal" (must be "high", "medium", "low", "max", true, or
false)` — the catalog lists a tier the route rejects and omits `max`, which it accepts.
It is not a live bug through the harness: both the bare selector and `:minimal`
returned `OK` via `omp -p` (2026-09-11), and `omp://provider-quirks.md` (Ollama) states
`mapReasoning` in `packages/ai/src/providers/ollama.ts` maps reasoning through
`model.thinking.effortMap`. What is measured is the pair of observations; the mapping is
the documented mechanism that explains them. → Probe tiers on the wire to learn what the
route serves, but confirm through `omp -p` before calling a tier broken; raw-API
behaviour is not harness behaviour.

**Leaderboard scores are effort-specific.** An AA page title pins the tier the score was
measured at. Comparing a `max` row against a `high` row is not a comparison.

**Indexes get rescaled.** Artificial Analysis v4.3 (read 2026-09-10) puts Opus 5 max at
51; the same model read 63 under the previous scale, and comments here quoted the old
number. A delta between a fresh read and a number in a comment is meaningless unless
both come from the same index version. Re-read both sides, or re-derive.

## Measurement artifacts

**Your own read timeout will masquerade as a model failure.** A 700 s client cap
recorded `glm-5.3-flash` at 3/4 and `glm-5.3` at 2/4. Re-running only the timed-out
cells at 1500 s turned glm-5.3-flash into 4/4 — that call finished in 111 s at lower
concurrency — while glm-5.3 stayed 2/4 with a *real* validator failure — a hunk header
of 5/6 against a body of 2/3. One of those two numbers was an artifact of the harness
and the other was the finding, and the pass would have pinned the wrong
model without separating them. → Retry every timeout at a higher cap before scoring,
and treat infra failures (HTTP 500, read cap) as unscored rather than failed. Retrying
one model's infra failure and not another's is how a bakeoff lies.

**An empty 200 is not a low score.** `openrouter/google/gemini-3.8-flash` returned
`finish_reason: "error"`, zero `usage`, and empty content on 3 of 4 bakeoff calls
(2026-09-11) — reproduced at 8K/32K/40K `max_tokens` and with an explicit provider
order, always from Google AI Studio. Scored naively that is "1/4", a quality verdict
the data does not support. → Read `finish_reason` and `usage` on every failure; an
upstream error is a reachability finding, not a ranking.

**`model_perf` decays, and a dead row freezes.** The table is a rolling window, not a
tally: `samples` is a fractional decayed weight (`zai/glm-5.3-flash` reads `148.03125`),
`ttft_samples` is a separate and smaller denominator (115.8 on that same row, so a TTFT
average divided by `samples` is ~22% low), and a model nothing routes to any more stops
updating instead of aging out. The costs, all 2026-09-11: an `n=428` cited from a
2026-09-10 read of `ollama-cloud/glm-5.3-flash` could not be found at all — the row had
re-averaged to n=140 and 2252 → 3671 ms, which read as a fabricated number; the same
row's advisor comparison was live-against-frozen, since zai last moved 2026-09-06 and
`opencode-go/glm-5.2` 2026-09-02, both flattered by retirement; and `gpt-oss:120b`
moved 207.7 → 201.9 tok/s *inside one session*, so a constant written into a config
comment was false before the turn ended. → Select `samples`, `ttft_samples` and
`updated_at` together (`commands.md`), quote a *direction* in config comments and keep
dated constants in one place, and treat any frozen row as unscored rather than fast.

**Never time the CLI.** `omp -p` pays ~8 s of startup before a request leaves the
process: a model with 345 ms TTFT still took 8.48 s that way, which is where a phantom
"fixed 10 s OpenRouter transport floor" came from. Raw curl answered 1.97–3.49 s. → Use
`omp bench` or curl.

**Concurrent `omp -p` deadlocks.** 16 parallel runs all timed out; even a 2-worker
harness stalled past 900 s. Serial runs are fine. → Run bakeoffs in-process, not by
fanning out CLI invocations.

**A bakeoff in an eval cell dies with the kernel.** An 18-call run returned
`[kernel] Python kernel shutdown` and every raw model output went with it — nothing
re-scorable, nothing to show for the wall time. → Write the harness to a file, run it
via `hub start` with a `ready` condition, and append each finished call to a JSONL as
it lands. A silent job is still checkable: `hub logs {name, follow: true, cursor}`
tails it from the last read cursor, and 0% CPU on a network-bound run is health, not
a hang.

**`omp bench` has its own path, and it fails where sessions do not.** Every
openai-codex model returns "Payment Required" under bench, yet answers ordinary session
calls on the same models — verified in both directions 2026-09-10 with
`omp -p --model openai-codex/gpt-6-astra "Reply with exactly: OK"` returning OK while
`omp bench openai-codex/gpt-6-astra` reported Payment Required. Never conclude a route
is dead from bench alone; confirm through the session path. The zai 429
`[1310] Weekly/Monthly Limit Exceeded` once filed here was real quota, not the bench
path: after the plan raise, 2026-09-24, `omp bench zai/glm-5.3-flash zai/glm-5.3` ran
4/4 clean. A bench 1310 means read `omp usage` first.

**An exhausted key fails selectively, which is worse than failing.** OpenRouter's key
was $0.09 past its 190 credits on 2026-09-10 and still answered 200 at 8, 256 and 2000
`max_tokens` — and at 8000 with no reasoning. The same 8000 with `reasoning: high`
returned 402 "This request requires more credits, or fewer max_tokens. You requested up
to 8000 tokens, but can only afford …", so the estimate that gets priced includes the
reasoning budget, not just output length. A cheap health probe therefore certifies a
route that cannot do the role's actual work, and `omp bench` — which caps output and
sends no reasoning effort — agrees with the probe. Check `/api/v1/credits` at the start
of a pass, and size any liveness probe like the work the role does, effort included.

**Reasoning mode can return nothing.** DeepSeek V4-Flash in reasoning mode hit its
output ceiling at 250 s+ on hard prompts with *no code emitted*, three attempts running.
With thinking off it was fast and merely wrong. A pass rate of 0/4 does not show up in
any index. → Execution-scored bakeoff.

**Validate the validator.** The diff validator's hunk arithmetic was wrong for
pure-insertion hunks — the `difflib` reference implementation failed it too. Every model
would have been scored against a broken oracle.

**A case every model fails identically is an ambiguous spec, not a defect.** Three
models answered that `a/**` matches `a`; the reference and `git check-ignore` said it
does not. The prompt sentence — "`**` matches zero or more whole path segments" —
genuinely permits both readings, so that case scored the prompt, not the model.
Unanimous failure on one case is the tell. → Tighten the wording, re-run, and keep the
raw outputs so the re-score is free.

**A second-opinion oracle needs its own config checked.** The `git check-ignore`
cross-check of the glob table reported four mismatches on macOS: `core.ignorecase`
defaults to true on APFS, so `[a-z]` matched `Q`. Set it false. One real mismatch
survived and was also not a semantic difference — git ignores children of an ignored
directory, so `/*` "matches" `a/b`.

**A hand-copied sqlite handle is what fails on a WAL database.** Copying only
`agent.db` misses the `-wal` and `-shm` siblings, so the copy shows stale or empty
tables. → Use the `read` tool's SQLite selector (`read agent.db:model_perf?q=SELECT
…`), which opens the live database and handles WAL correctly.

**Catalog `int`/`tps` fields are not measurements.** They are vendor-supplied numbers
carried in the bundled catalog. Quoting them as evidence for a quality ordering is the
most common way this review goes wrong.

## Sources

**Leaderboards are client-rendered.** OpenRouter's Coding Index does not exist in
static HTML: a plain fetch greps zero hits and looks like an empty leaderboard.
Artificial Analysis is the same class of page. → `eval`'s `browser`:
`browser.open`, wait for the render, `tab.scrollIntoView`/`tab.evaluate` to reach
`#benchmarks`, `tab.ariaSnapshot()` to read what actually rendered.

**Slugs and pages disappear.** AA's `artificial-analysis-coding-index` evaluation page is
retired; `qwen3-5-flash` 404s where `qwen3-5-omni-flash` resolves. A 404 is a wrong
guess, not an absent model.

**Chains cannot buy concurrency.** `providers.<p>.maxConcurrency` is a queue limit, not
an error, and fallback chains fire on failure. A 32-agent fan-out serializes into waves
regardless of what the chain says; widening it means re-pointing the role at an uncapped
(metered) provider at the highest-volume point in the system.

**A subagent's claim is not evidence.** One reported the advisor never fired because a
bench showed `spawns=0`; `spawns` counts `task` tool calls, and the advisor is not a
spawn — its journals existed for every run. Verify against primary evidence.
