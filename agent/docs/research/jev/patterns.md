# Patterns: typed judgment beyond the safety guard

Sources: TypeSafe's own docs/cookbooks (primary), the LangChain integration write-up, the Jev launch post + workflow evals site, MCP spec pages (primary), a handful of GitHub proxies/benchmarks, and tool-selection research papers. Every claim is labeled **[observed]** (a measured number the source published, or code we inspected) or **[claimed]** (a README/vendor assertion). URLs and paths inline. Secondary write-ups are marked as such.

## Bottom line

- The two patterns with published, transferable, harness-relevant evidence are **roster shortlisting** (TypeSafe's skill-suggestion cookbook: 2 requests/turn, wrong loads 16.8%→7.3% on 182 candidates, [observed]) and **cascade verification of an extractor's claimed work** (SDE cascade; schema-valid-but-fabricated records are the target). Both have real code.
- Tool-call gating over a **small** surface (LangChain's AutoModeMiddleware over `bash`) works and mirrors what we already have; a Jev **tool-shortlist over ~80 mounted tools is not worth building** — evidence says accuracy degradation bites far above 80 tools for modern models, our lazy docs-on-demand already solves exposure, and MCP itself added `ttlMs` list caching so mounted schemas cost less than assumed.
- Composite scoring / confidence-gated thresholds are cheap to add and well-supported by docs, but for our harness they are **already-have** in the routing/guard commands' threshold logic; nothing new to build.
- Extraction (pre-parsed pick, date parts, entity alignment) is the family most transferable to a coding agent: `choice` over candidate spans/paths is the shape that replaces prompt-and-parse. Highest-value candidate: candidate-span picking over grep hits and file lists.
- Anti-patterns to avoid, all first-party: counting/arith/dates in Jev (jaggedness page), trusting nouls near 0.5, carrying thresholds across question types, treating Noul↔Choice as complements, and sending more state than the question needs (context rot). Third-party tool descriptions are untrusted input for a judgment layer (injection surface), same class as fetched web content.

---

# A. Patterns from TypeSafe's own cookbooks (primary, with code)

Every cookbook below is `https://docs.typesafe.ai/cookbooks/<slug>.md`, run against `jev-1.12`/`jev-1.13` with shipped result caches; numbers are [observed] as published by TypeSafe.

## A1. Intent routing / dispatch

- **Shape:** state = the message (string); questions = one `choice` over intent labels + one `score` for complexity/hardness. One call.
- **Code sketch** (docs.typesafe.ai/patterns/intent-routing, routing.py):
  ```python
  intent = answers["intent"]          # choice: order_status | product_question | return_exchange | complaint
  complexity = answers["complexity"]  # score: simple lookup → escalation needed
  if intent.confidence < 0.5:
      route_to_human_agent()
  elif intent.choice == "order_status":
      handle_order_status()           # deterministic code, no LLM
  elif intent.choice == "complaint" and (complexity.score > 1 or complexity.confidence < 0.5):
      route_to_human_agent()
  else:
      handle_with_llm(ticket_id, SPECIALIST[intent.choice])
  ```
- **Replaces:** a "classify this message and pick a handler" LLM prompt. One of four intents routes to zero-LLM code; two route to cheap specialist models; one uses the score as an LLM-vs-human switch.
- **Failure mode:** low-confidence *complexity* still escalates (good); but intent labels that are near-synonyms will bleed probability. Doc guidance: a low confidence floor (0.5) before any route; per-branch thresholds scale with consequence (confidence-routing pattern uses 0.6 for read-only, 0.85+ for a transfer).
- **Status for us: already-have.** Our `route` command picks a subagent the same way. The one borrowed idea: gate *handler difficulty*, not just identity, and route on `complexity.score` too.

## A2. Speculative fan-out

- **Shape:** all questions (including branch-specific ones) in one call; code consumes only relevant answers. Support-ticket example asks `bug_severity` and `has_reproducible_steps` even when the ticket may be a feature request (patterns/fan-out, triage.py).
- **Cost claim:** questions evaluate in parallel; "adding more questions usually has little effect on response time" [claimed by docs; consistent with our measured 111 ms mean for a 14-question rubric — consistency_noul cookbook, [observed]]. Hard budget: 64k tokens/request total, 32k for state + longest question (models.md, [observed]).
- **Replaces:** sequential classify-then-ask round trips.
- **Failure mode:** token cost scales linearly with question count even when answers are discarded; questions irrelevant on most turns are pure waste. The skill-suggestion cookbook gates this with nouls ("need a skill at all?") rather than asking speculatively about every branch.
- **[actionable]** For an always-on layer: ask the "does anything apply at all" gate noul in the same call as the ranking, so idle turns cost one cheap request, not zero requests but also not two.

## A3. Roster shortlisting (choice-over-N + gate nouls, then rerank top-K) — the pattern closest to tool routing

- **Source:** cookbooks/skill_suggestion.md, rendered 2026-07-31, `jev-1.12` + `claude-haiku-4-5-20251001`, 488 requests over 182 Hermes skills. All numbers [observed] as published.
- **Shape, request 1:** one `choice` whose criteria are all 182 skill names → one-line descriptions (index text, ~54 chars avg); plus three gate nouls on the *request* ("acts on user's system?", "would consult documented procedure?", "prose suffices?" inverted). Mean of oriented nouls ≥ 0.30 else suggest nothing.
- **Shape, request 2:** same `choice` over the top-3 only, criteria now full description + 700 chars of SKILL.md; plus one `fits::<name>` noul per candidate ("does this skill do the specific thing asked?"); shortlist dropped if best fits < 0.30.
- **Result:**
  | arm | wrong loads | needless loads |
  |---|---|---|
  | agent alone (60-char index) | 16.8% | 9.8% |
  | + TypeSafe suggest | 7.3% | 4.0% |
  | oracle (handed answer) | 2.5% | 1.2% |
  2.3× fewer wrong loads, 2.4× fewer needless. 37 fixed vs 7 broken — "a confident wrong suggestion is more persuasive than no suggestion" [observed].
- **Replaces:** an LLM picking from a truncated index ("err on the side of loading" prompt).
- **Failure mode:** the two `.pptx` lookalikes — the wide choice ranks the wrong one on 60-char descriptions; only the rerank with full text flips it (0.700 powerpoint → 0.700/0.300 split resolves to pptx-author). Also the Mastodon case: gate nouls say "action wanted", no real skill exists, closest skill (X posting) wins anyway — gate can't catch wrong-domain misses.
- **Key wording guidance** (first-party): "A question about subject matter will not separate *explain what a monad is* from a request that needs a skill… Write these to ask whether an action is wanted." Gate questions ask about the *request*, not the roster.
- **Scalability guidance:** "One `Choice` question holds a roster this size comfortably. A few times larger and you would split it into chunks and rank each one, then run this same shortlist step over the winners." [claimed, TypeSafe]
- **[actionable]** This is the one pattern directly reusable for tool/skill/subagent selection at scale. Two thresholds + shortlist + "suggestion is advisory" phrasing ("Ignore this if it does not fit") are all load-bearing.

## A4. Verification of claimed work (cascade) — verify-then-escalate

- **Source:** cookbooks/sde_cascade.md (2026-09-15 prices). [observed] structure, [claimed] quality/cost summary.
- **Shape:** cheap LLM (gpt-5.4-mini) extracts fields from a page into a JSON schema; Jev verifies with per-field `noul` batteries keyed `field::metric` — `hallucinated` ("unsupported by, or absent from, the source text"), `off_target` ("value was pulled from incidental text"), `unreasonable`, `incomplete` (empty field when source has it), `format_violation`, plus an `absence_wrong` head for empty fields; one holistic `__overall__::judge` noul is displayed but deliberately *not* used for the gate. Escalate to gpt-5.5 if any per-field P(wrong) > 0.7.
- **The demonstrated failure it catches:** a schema-valid extraction whose `description` is fabricated ("Registration opens for the fall semester" parroted from the schema's own example) on a page with no such content — `jsonschema` validates it as `True`; only the semantic battery flags it. Verifier flagged that exact fabrication at P(wrong) > 0.8.
- **Replaces:** "ask the big model to re-extract" or human review of every record; escalates only flagged records.
- **Failure mode:** `type_mismatch` skipped when the schema type is unknown; hard-coded canonical extraction in the walkthrough (mini is too stochastic at t=0 to demo reproducibly); the authors note they intentionally avoid structured outputs/tool calls so as not to mask the target failure class.
- **[actionable]** This is the direct analogue of "verify the agent's own claimed work" in our harness: before accepting a subagent's summary, ask per-claim nouls against the diff/artifacts. The framing trick: questions are phrased so `true` = *something is wrong* (escalate), and empty fields get only the absence head.

## A5. Citation check (self-verification of citations)

- **Source:** cookbooks/citation_check.md (2026-08-16, RFC 7519). [observed].
- **Shape:** string-match the quote into the source first (fabricated = mechanical, no model); survivors get one 3-way `choice` — supports / contradicts / says_nothing — over claim + section; confidence ≥ 0.8 auto-accepts, below goes to human. All four planted failures caught (fabricated quote by regex; contradicted + 2 unsupported by the choice); 4 accurate ones `verified` at conf ≥ 0.93.
- **Replaces:** human citation audit. **Failure mode:** a quote present verbatim but contradicting the claim is exactly the case the model step must catch; the threshold 0.8 is "start high for more human review as you build trust".
- **[actionable]** Same shape as A4 for verifying an agent's citation of code/files: `grep` to confirm the quote exists (cheap, exact), Jev to confirm the context supports the claim.

## A6. Composite scoring (weighted rubrics)

- **Source:** patterns/composite-scoring (resume screening). One request, four `score` questions, each with 5 written levels; code normalizes `/4` and applies role weights (IC vs EM) in plain Python.
- **What it replaces:** a single "rate this candidate" LLM judgment; visibility into the composite ("adjust weights without re-running inference") is the selling point.
- **Failure mode:** score levels must "describe concrete situations and stand on their own"; scores are weak in numerical calibration (jaggedness: "do not interpolate a number between two levels") — composite arithmetic is fine, magnitude interpretation is not.

## A7. Confidence-gated routing (two-axis thresholds)

- **Source:** patterns/confidence-routing + concepts/confidence. [claimed/design guidance].
- **Shape:** intent `choice` + action-specific thresholds: < 0.6 → human; balance at 0.6; transfer needs > 0.85 else confirm-with-user.
- **Anti-pattern guidance (confidence.md):** a noul near 0.5 is "similar probability for yes and no, not medium intensity"; low choice confidence can mean *several acceptable options*, so it need not invalidate a harmless choice; "ignore uncertainty on unused branches."

## A8. Extraction family (pick-don't-generate)

- **Pre-parsed value extraction** (cookbooks/pre_parsed_value_extraction_cookbook.md): regex over-finds candidate spans (emails, phone, money), `choice` picks the requested one verbatim or `none`; code normalizes (E.164, Decimal). All three demos correct at confidence 0.90–1.00 [observed]. The model "cannot invent a value or transpose a digit" because options are the spans.
- **Date extraction** (cookbooks/date_extraction_cookbook.md): 7 `choice` questions (mode/month/day/year/anchor/weekday/offset), `none` and `out_of_range` escape hatches on every part; code owns calendar math; weakest-part-confidence gates review at 0.60. This is the doc-jaggedness pattern ("extraction is a judgment; arithmetic is not") in code.
- **Entity alignment** (cookbooks/entity_alignment.md): one 3-level `score` (different / related→curator / same→merge) over candidate pairs; *no threshold to fit* — round to nearest level; three companion nouls (same name/brewery/style) annotate the curator queue. Merge errors are more expensive than misses, so the ordered middle level is the whole design. 450 beer pairs, one request each.
- **Hierarchical classification** (cookbooks/hierarchical_classification.md): deep taxonomies (CPC patents, Shopify, MeSH, a codebase!) via per-node `choice` over direct children, parallel beam K=3 kept by geometric-mean edge probability, `separation = top/second` path ratio as ambiguity metric; beam 4/4 correct, greedy 2/4 [observed]. The codebase hierarchy demo ("find the module implementing BM25 retrievers" → `retrievers.py`) is the closest thing to codebase navigation by typed judgment.
- **[actionable]** Pick-over-candidates is the pattern to steal for harness "point at the file/spans" moments: grep for candidates, `choice` to pick, code to copy. Never let Jev generate identifiers.

## A9. RAG passage screening (injection + conflict routing)

- **Source:** cookbooks/classifying_rag_passages.md (2026-08-27, Supabase auth docs, 81 passages). [observed].
- **Shape:** embedding retrieval top-12 → per-passage one request, 4 nouls (relevant? usable evidence? contradicts query premise? prompt injection?) → thresholds (injection_max 0.70, contradicts_min 0.70, relevant_min 0.45, evidence_min 0.55) → route into evidence / conflict / drop blocks.
- **Notable numbers:** planted forum injection ranked **1st** by cosine similarity (0.584 vs 0.455–0.576 band) — "a spread too narrow to separate the passage that corrects the query from the one trying to hijack the answer." Embeddings alone put the hijack on top; the noul battery is what catches it.
- **[actionable]** Directly relevant to our `screen` command for fetched content: keep + *flag contradicting* passages separately rather than dropping, so the model can correct a false user premise instead of ignoring it.

## A10. Self-consistency / uncertainty bands

- **Source:** cookbooks/consistency_noul_cookbook.md (2026-09-11, jev-latest→jev-1.13.0, 14-question rubric ×15). [observed].
- **Numbers:** Jev mean per-question std 0.0102 — *more* self-consistent than every LLM condition, including temperature 0 (haiku t=0: 1.78 s, $0.0018; Jev: 111 ms, $0.000043, 42× cheaper). But Jev's `covered` answer spanned 0.43–0.53 across repeats, crossing a 0.5 threshold.
- **Guidance:** don't force yes/no at 0.5 — map < 0.30 → no, 0.30–0.70 → `uncertain` (human review), > 0.70 → yes. The band "is neither a calibrated guarantee nor an optimized threshold"; set production boundaries from labeled examples and the cost of wrong decisions.
- **[actionable]** For our always-on guard: a review band absorbs 0.49-vs-0.51 flapping without issuing opposite actions — this is the alert-fatigue fix.

## A11. Guardrails battery (adjacent to our guard — for deltas only)

- **Source:** cookbooks/llm_guardrails.md (2026-08-15). One request per message: hazard nouls (jailbreak, harm/crime, medical, self-harm) + one severity `score`; named policies map hazard→action with a review threshold and an action threshold, precedence pass<review<block<support. Both input *and output* screening.
- **Our `guard` covers the pattern; the deltas worth stealing:** (1) named threshold policies ("strict"/"permissive") as a versioned dict, not scattered constants; (2) severity score can upgrade review→block; (3) screen outbound replies too, not just inbound.

# B. Tool-call routing with typed judgment (user-priority section)

The thesis under test: if Jev can reliably pick the right tool from a catalogue of descriptions, a harness can mount far more tools than fit comfortably in context, surfacing only the relevant few per turn.

## B1. Does anyone actually do dynamic/lazy tool exposure? Yes — abundantly, and almost none of it with a generative-LLM or judgment-model classifier

Real implementations, with what the selector actually is:

| Implementation | Selector | Notes |
|---|---|---|
| Claude Code MCP Tool Search (Anthropic feature) | dynamic discovery, search-and-load | "reduces token overhead by 85%" [claimed, per atcyrus.com write-up of Anthropic's feature — secondary source] |
| [MCProxy](https://github.com/igrigorik/MCProxy) `docs/SEARCH.md` | **Tantivy full-text/BM25** over names+descriptions; `maxToolsLimit` 50 default, auto-injects a `search_available_tools` tool, BM25 threshold 0.1 | [observed, code+docs] |
| [Portkey-AI/mcp-tool-filter](https://github.com/Portkey-AI/mcp-tool-filter) | **embedding similarity**, 1000+ tools → 10–20 in <10 ms [claimed, README] | |
| [ImBIOS/tool-search-mcp](https://github.com/ImBIOS/tool-search-mcp) | **Ollama embeddings + BM25 + regex**, "save 97% tokens" [claimed, README] | client-side for Claude Code |
| FastMCP [search transform](https://gofastmcp.com/servers/transforms/tool-search) | replaces `list_tools` with synthetic `search_tools` + `call_tool` pair | [observed, docs] |
| [kais-radwan/mcp-tool-filter](https://github.com/kais-radwan/mcp-tool-filter), [pro-vi/mcp-filter](https://github.com/pro-vi/mcp-filter) | **static whitelist** — no ML at all | [observed, READMEs] |
| Semantic-tool-discovery paper (arXiv 2603.20313) | ada-002 embeddings, K=3 | hit@3 97.1%, MRR 0.91, <91 ms, 99.6% token reduction [observed, published benchmark of 140 queries / 121 tools / 5 servers] |
| Writer's RAG-MCP instrumentation (via tianpan.co, 2026-04-19 — **secondary, blog**; original RAG-MCP paper exists) | embedding retrieval over tool descriptions | baseline tool-selection accuracy 13.62% on a large catalog → 43% with retrieval [claimed, secondary] |
| MCP proposal discussions ([modelcontextprotocol#643](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/643), cline#3081, Roo-Code#2893) | assorted: single search tool, embeddings+confident-call classifiers | [observed, discussion texts] |

Pattern: **nobody's production tool-selection layer is an LLM/judgment call.** It's embeddings, BM25, or a static whitelist. The judgment-model-shaped slot in these architectures is at most a stage-3 reranker on 20–50 candidates (olejardamir/Dynamic_MCP README explicitly suggests a strong classifier "as the last ML narrowing step on the top 20–50 candidates, before the main LLM sees only 5–10 tools" [observed, README text]).

## B2. Published evidence on degradation vs tool count — the load-bearing question

- **LongFuncEval (arXiv 2505.10570, 2025-05):** with tool catalogs grown to 65,536 and 120,000 tokens of context, accuracy deteriorates across models; Mistral-large drops 94%, BitAgent-8B 82.37%; with ~200 tools (32K tokens) accuracy 41–83% depending on model, ~740 tools (120K tokens) 0–20% [observed, paper].
- **Position bias:** middle-of-list tools selected correctly 22–52% of the time vs 31–32% at start/end (vLLM semantic-router blog, 2025-11 — secondary summarizing "lost in the middle" research) [claimed, secondary].
- **Semantic distractors cost 1–8% accuracy** on function-calling benchmarks (TMLS tool-use-reliability page — secondary) [claimed, secondary].
- **Production-rule-of-thumb claims:** degradation "measurable once tool counts pass roughly 10–15", production teams see drops "once they cross 15–20 tools", practical ceiling 30–50 (machinelearningmastery.com guide, 2026-07-06 — **secondary, blog; treat the small numbers skeptically**). OpenAI documents a hard ceiling of 128 tools per request.
- **Crucial read for our verdict:** all the hard degradation numbers live at catalog sizes ≥ ~200 tools / ≥ 32K tokens of schemas. Nothing in the primary literature shows a modern frontier model failing at 80 tools ≈ 16–40K tokens *of dense schema* — and schemas are cheap to make dense. The famous failures are either 100s+ of tools or weak/small models.

## B3. Which Jev question type fits, and its limits

- One `choice` with N tool labels works to **N ≈ 255**: "Jev supports a cardinality up to 255. For the higher cardinality choices, we do a 2 stage-system of scoring independently then making an explicit choice, hence the occasional slowdown" (launch post, Fun Demos: Wikiracing, [claimed by TypeSafe]). The skill-suggestion cookbook held 182 labels "comfortably" and advises chunking "a few times larger" [observed, TypeSafe].
- N parallel `noul` relevance questions (one per tool) also works and gives an absolute filter — but that's exactly the two-pass shape A3 already showed is better used as wide-rank → rerank-top-3 with absolute `fits` nouls.
- Cost scale: Jev input is $42/Btok ($0.042/Mtok), output free (models.md). A 80-tool shortlist with 60-char descriptions ≈ index text of ~10–16K chars ≈ 3–4K tokens ≈ **$0.00015/call**; a full 80-tool schema catalog at ~500 tok/tool ≈ 40K tok ≈ $0.0017 if you *sent it to Jev* (you wouldn't — that's the LLM's context cost, not Jev's).
- Latency: ~100 ms typical, measured 111 ms mean on a 14-question rubric, 0.09–0.31 s on the skill-suggestion calls [observed].

## B4. Failure modes of shortlisting — and how to fail open

- **Hard dead end:** if the right tool is not in the shortlist, the model cannot invoke it; worse, the *rerank* stage can only reject what the wide pass handed it (skill-suggestion: the Mastodon request survived both checks because the X skill was the only plausible candidate). The paper's failure modes: ambiguous queries ("help me with my project") retrieve a mixed set; semantically overlapping tools (filesystem read/write/copy/move) confuse retrieval; cross-domain queries ("commit the DB schema changes to GitHub") need two servers' tools and a single query misses one (arXiv 2603.20313 §6.2 [observed]).
- **Failing open:** the paper's own graceful-degradation design — fall back to top-K regardless of threshold when the filtered set is empty; alternative: fall back to the all-tools baseline on low confidence [observed, §6.4]. MCProxy's shape is fail-open too: exposure starts at a cap and *grows* via search. For a harness: never hard-hide — mount a stable core set (read/search/edit), expose the tail via `search_available_tools`-style discovery, and let a failed/low-confidence shortlist widen the surface rather than shrink it. Keep our docs-on-demand escape hatch (any named tool's schema is fetchable) so a missed shortlist is recoverable by a docs lookup.
- **Injection surface (remote servers):** a tool description arriving from a third party is untrusted input; a judgment layer *reading* descriptions to route is itself steerable (jaggedness: "State is data… content written to adversarially steer the model… can move the answer"; the RAG cookbook's whole point is that retrieval surfaces injections on top of relevant results). Handling: treat descriptions like fetched web content — run the same injection screen before they influence selection; never let a description's imperative text become an action; and note the MCP spec's own position: "clients **MUST** consider tool annotations to be untrusted unless they come from trusted servers" (spec 2025-06-18 server/tools) [observed, primary].

## B5. MCP protocol reality for web/remote servers

Direct from the spec, not blogs:
- **Pagination** exists on `tools/list` (cursor-based, spec 2025-06-18 server/tools [observed]) — so a client can enumerate thousands, but pagination solves transport, not selection.
- **`listChanged`** capability + `notifications/tools/list_changed` exist so clients can refresh catalogs when servers change tools [observed].
- **2026-07-28 spec (current):** stateless core; `server/discover` mandatory RPC; **`ttlMs` and `cacheScope` hints on `tools/list` results**; deterministic tool ordering to keep upstream prompt caches stable across reconnects (MCP blog 2026-07-28 release posts; Cloudflare mcp-v2 post) [observed, primary].
- **No protocol-level tool search:** searches of the 2026-07-28 spec find no standardized `tools/search`; search transforms (FastMCP, MCProxy) are server/proxy-side conventions built on synthetic tools [observed, absence].
- Gateways that select across many servers: MCProxy (BM25 above), FastMCP transforms, Portkey embeddings. All same conclusion as B1.

## B6. Cost arithmetic: per-turn `choice` over N labels vs paying schema tokens

Assumptions (stated): 80 tools × ~500 tok schema ≈ 40K tokens in context; prompt-caching makes steady-state marginal cost of that context small (cached-read rates on frontier models run ~10% of input price); 1 turn ≈ 1 Jev call with state = user turn + 80 one-line descriptions ≈ 4K tok.

- Jev selector: 4K tok × $0.042/Mtok ≈ **$0.00017/turn** + ~100 ms — negligible in money, real in added latency/complexity, and *nonzero error rate* on top of a model that would have picked from 80 anyway.
- Schema tokens: at frontier non-cached input (~$1.5–5/Mtok), a cold 40K-tool-context ≈ $0.06–0.20 uncached; with prompt caching the *marginal* per-turn cost drops by an order of magnitude. But token count in context is also the **accuracy** budget, and LongFuncEval shows problems appear somewhere past ~32K of tool catalog. 80 tools ≈ 40K tok is right at that edge — the strongest honest argument *for* some filtering is accuracy-at-context, not money.
- **Crossover:** the selector pays for itself in tokens only when (tools × 500 tok) exceeds (selector cost + shortlist exposure) × cache factor — i.e. catalogs of **several hundred-plus tools** with long schemas and no prompt-cache reuse. At 80 mounted tools with docs-on-demand, it never does.
- **[actionable]** If we ever cross ~200 tools (e.g. by subscribing to many web MCP servers), the boring stack wins: embedding/BM25 shortlist (free, <100 ms, proven hit@3 ≈ 97%) → optionally a Jev *rerank of the top ~10–20* (the only shape where a judgment call adds precision that embeddings lack: overlapping descriptions) → never a bare N=80 `choice` per turn.

## B7. Blunt verdict on tool routing

For a single-user laptop harness with ~80 MCP tools and lazy schema docs: **skip the Jev tool selector; already-have the exposure mechanism; build nothing now.** Modern coding models pick fine from 80 tools; our docs-on-demand is the progressive-disclosure layer; MCP's `ttlMs` list caching now makes mounted catalogs cheaper to keep mounted; and every real gateway in the wild does this with embeddings or BM25, not judgment calls. The one conditional: if web-MCP subscriptions push the catalog past a few hundred, the right design is retrieval-shortlist + optional Jev rerank, with fail-open fallback — not a per-turn `choice` over the world.

# C. Other real-application patterns (beyond TypeSafe docs)

- **LangChain harness middleware (langchain.com/blog/building-a-harness-with-jev, 2026-09-17, first-party LangChain):** two shipped middleware shapes. `ModelRouterMiddleware` — Jev picks "fast" vs "powerful" model per request from the user message ("Choose the least costly model that can complete the task"), choice criteria describe each model; probabilities kept in agent state. `AutoModeMiddleware(tools=["bash"])` — Jev checks tool calls for risk *before* execution, i.e. our `guard`, generalized to any agent. [observed, code sketch in post]
- **Early-adopter claims (launch post + LangChain recap, [claimed]):** Browserbase powering browser-use agents "for fractions of a cent" (Kyle Jeong), a live trading agent (Jarrod Watts), email triage at scale (Ryan Vogel). No published code or numbers; treat as anecdotes.
- **Doom-playing bot (launch post):** ~10 judgments/second ≈ **~$7/hour** [claimed by TypeSafe, with the engineer's own cost surprise noted]. The interesting bit: reactive typed judgment over game state at 100 ms cadence — the "interactive loop" pattern; not useful to a coding harness, but it's the latency envelope's existence proof.
- **Workflow evals (evals.typesafe.ai, primary):** four production-shaped workflows (security incidents, agent-trace observability, invoice processing, customer service) run as decomposed harnesses; Jev at 67.8% mean accuracy for $0.0004/case and 0.4 s, vs opus-5 workflow 73.1%/$0.176/37.8 s and Jev's own prompt-mode at 18.1% [observed, published table]. Two directly harness-relevant workflows: **agent-trace observability** ("given the whole run, every tool call included, decide whether a person needs to look, and how soon") — exactly a `stuck`-class command — and security-incident triage (close/analyst/contain-now).
- **Community extensions:** already surveyed (pi-jev, jev-guard, etc.) — not re-reported.

# D. Calibration, wording, and anti-pattern guidance (published)

All first-party unless noted:

- **"Serves the ask" vs "was literally asked"** — Jev is literal; it answers the written condition, not the intent (jaggedness #1: "when you look at a wrong answer and find yourself explaining what you really meant, that explanation is the missing half of the instruction"). Where interpretation is unavoidable: split into two literal questions and combine in code. The function-calling cookbook's `stated` question is this distinction operationalized: ask separately "did the user say anything about X at all" before asking "which X" — without it the model "would have named [a window] confidently."
- **Thresholds are domain data, not constants:** "Start with conservative thresholds, test with your own data" (confidence.md); cookbook thresholds are "examples to evaluate, not universal rules" (skill text); citation-check starts at 0.8 auto-accept "for more human review as you build trust."
- **Don't carry thresholds across types:** Noul and Choice answers "are not directly comparable… don't rely on expected structural invariance" — the refund question scored noul 0.22 while its yes/no choice said 0.99 no; `refund`+`not_refund` nouls summed to 1.19 (jaggedness #8) [observed].
- **Alert fatigue for always-on layers:** (a) explicit `uncertain` review band instead of 0.5 snap (A10); (b) gate-first architecture — a "does anything apply" noul before any suggestion, so the common case is silence (A3); (c) suggestion wording that explicitly authorizes ignoring ("Ignore this if it does not fit what the user actually asked for") because "pushing harder wins compliance on wrong suggestions too" (A3); (d) empty-branch tolerance — "ignore uncertainty on unused branches."
- **Score ≠ magnitude; arithmetic ≠ judgment:** never interpolate numbers from score levels; compute in code (jaggedness #2). Counting is unreliable; iterate candidates and ask one noul each, sum in code (jaggedness, worked example).
- **Context rot:** accuracy falls as state fills with irrelevant detail; "retrieve and filter in code first, and send only the fields the question needs" (jaggedness #5). Also the hard 32k state+question budget (models.md).
- **Confidence semantics:** choice confidence is distribution concentration, not workflow correctness; "low confidence need not invalidate a harmless preference choice" (skill/docs skill text); a noul near 0.5 means yes/no coin-flip, not medium intensity.
- **Adversarial state:** "State is data, and jev-1.13 does not treat it as hostile by default" — injected instruction text in state can move answers (jaggedness #6). For a guard layer this is the honest ceiling: an attacker who can write the *state* has some leverage over the classifier judging the state.

# E. Verdict table for our harness

Already have: `route` (subagent choice), `guard` (destructive ops), `screen` (prompt-injection), `stuck` (loop detection), `ask`, JSONL logging. Verdicts:

| Pattern | Verdict | Why (one line) |
|---|---|---|
| Intent routing to handlers (A1) | already-have | `route` is this; steal only the complexity-score LLM-vs-human switch. |
| Speculative fan-out + gate nouls (A2) | **build (cheap)** | One extra "does anything apply" noul per call makes our always-on layer mostly-silent; costs ~0.1 ms-equivalent tokens. |
| Roster shortlist wide-rank→rerank (A3) | **build, but for skills/subagents — not tools** | Our agent/skill roster is where truncation-induced mispicks are real; 182-label evidence transfers directly. |
| Verify claimed work, per-claim noul battery (A4) | **build** | Schema-valid-but-fabricated is exactly what a subagent summary can be; per-claim `hallucinated`/`off_target` nouls against the diff is the highest-value addition. |
| Citation/claim string-match + choice (A5) | **build (fold into A4)** | `grep` confirms the quote exists; Jev confirms the context supports it — two lines on top of A4. |
| Composite weighted scores (A6) | skip | We have no multi-dimension ranking decision; weights without a consumer are decoration. |
| Confidence-gated thresholds (A7) | already-have | Guard/route thresholds exist; add the named-policy-dict hygiene only. |
| Pick-over-candidates (grep hits, files) (A8) | **build** | Cheapest real win: Jev never types an identifier; replaces "LLM, which line was it?" prompt-and-parse. |
| RAG-style injection screen with conflict flagging (A9) | build (small) | Extend `screen`: keep+flag premise-contradicting content instead of only dropping injections. |
| Uncertainty band on always-on nouls (A10) | **build** | Kills 0.49/0.51 action flapping in guard; the alert-fatigue fix, ~5 lines. |
| Guardrails battery (A11) | already-have | Ours exists; adopt named threshold policies + screen outbound agent messages too. |
| Tool-call shortlist over ~80 mounted tools (B) | **skip** | Degradation evidence bites ≥ ~200 tools/32K tok; our lazy docs-on-demand already does progressive disclosure; every real gateway uses embeddings/BM25, not judgment calls; a per-turn choice adds latency and an error rate for ~$0.0002 of token savings we don't need. |
| Per-turn Jev selection for web-MCP at scale (B6) | skip now, revisit >~300 tools | At that point: embedding shortlist → optional Jev rerank of top 10–20, fail-open to exposing more; not a bare N=80+ choice per turn. |
| Game/interactive loops (C) | skip | Existence proof for latency, not a harness use. |
| Agent-trace observability command (C/evals) | **build** | TypeSafe's own eval treats "should a human look at this run" as a first-class typed workflow; our `stuck` detects loops, not quality. |
| Counting/numeric/date judgments (D) | skip (anti-pattern) | First-party: Jev doesn't count, compute, or compare dates; keep arithmetic in code. |

# F. Gaps / not found

- **No third-party production code** found doing tool selection *via* Jev (searched GitHub proxies listed above, MCP spec, MCP proposal discussions, LangChain docs): every real selector is embeddings, BM25, or a whitelist. If someone has built a Jev tool-router, it is not public as of 2026-09-22.
- **No published independent benchmark of Jev accuracy** vs its claims beyond TypeSafe's own evals and cookbooks (their own numbers are cached replays, not live reruns by third parties). Tom's Hardware / MarkTechPost / dev.to / getmaxim pieces are all secondary restatements of the launch post; none add measurements.
- **No numbers on choice cardinality between 255 and 64k:** the 255 cap is from the launch post (Wikiracing demo) [claimed]; the "a few times larger than 182 → chunk" guidance is cookbook prose. We found no systematic study of accuracy vs option count for Jev.
- **No public code for the "2-stage scoring for high-cardinality choices"** the launch post mentions.
- **Tool description quality:** research cited claims "a high number of MCP tool descriptions contain at least one quality issue" (machinelearningmastery, secondary) — no primary source located.
- **Rate limits "adjusting dynamically"** (models.md warning, undated beyond page state) — any always-on per-turn design must assume limits move under you.
- **Untrusted-content advisory found in fetched content:** none of the pages/repos read contained instructions aimed at AI agents; the MCP spec's own trust warnings are quoted in B4. One cookbook image filename (`this_is_the_way.jpg`) is stylistic, not an instruction.