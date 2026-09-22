# Jev / System One API — First-Party Facts

Retrieval date for all sources: **2026-09-22** unless noted on the line. Everything below is from first-party sources (docs.typesafe.ai, typesafe.ai legal pages, api.typesafe.ai OpenAPI, first-party SDK source on GitHub/npm/PyPI, status.typesafe.ai). Labels: **[observed]** = source states a measured/authoritative number or we fetched the artifact; **[claimed]** = marketing/README assertion not independently verified.

## Bottom line

- Exactly three question types exist — `noul`, `choice`, `score` — confirmed by docs, the OpenAPI spec at `https://api.typesafe.ai/openapi.json` (v0.2.0), and the JS SDK `Question` union (`src/types.ts`, tag `v0.6.0`). No fourth type is documented anywhere in the index.
- `jev-latest` → `jev-1.13.0` (models page, 2026-09-22). `jev-preview` also currently → `jev-1.13.0` with a first-party warning that no preview build exists. No published model deprecation list.
- The "~32k token" belief is now first-party confirmed, with a correction: **64k tokens per request total; 32k applies to `state` plus the single longest question** — the rest of the questions share the remaining 32k budget (models page).
- Billing is **input tokens only** ($42/Btok = $0.042/Mtok); output tokens are "currently free" (OpenAPI Usage schema). No free tier page exists; free use is only "Promotional Credits" at TypeSafe's discretion under the MCA.
- Our client's "HTTP status errors are non-retryable" stance contradicts first-party SDK behavior: both official SDKs default-retry **408, 429, and all 5xx** (529 included), plus connection errors and timeouts, max 2 retries, 500ms→5s backoff, honoring `Retry-After`/`retry-after-ms` up to 60s. **[actionable]**
- Docs and sources disagree in a few places (Score min-levels, whether `instructions` is required, Python timeout default); each is flagged inline below.

---

## Question types and answer shapes

Source: API reference https://docs.typesafe.ai/api.md (2026-09-22); OpenAPI spec https://api.typesafe.ai/openapi.json (2026-09-22); JS SDK source https://raw.githubusercontent.com/typesafe-ai/typesafe-sdk-js/v0.6.0/src/types.ts (tag `v0.6.0`, 2026-09-22).

**Request** (`POST https://api.typesafe.ai/v1/systemone`, Bearer auth):
- `state`: string | object | array — required. **[observed]** (OpenAPI `SystemOneRequest`)
- `model`: string — required. Versioned IDs are accepted "whether or not they appear" in `GET /v1/models` (models page).
- `questions`: map<string, Question>, `minProperties: 1` — required. Keys are client-chosen; "The key is not sent to the underlying model and is not used in inference." **[observed]** (OpenAPI + api.md)

**Question schemas** (per OpenAPI; JS SDK `NoulQuestion`/`ChoiceQuestion`/`ScoreQuestion` in `src/types.ts`):
- Noul: `{ type: "noul", instructions?: string|object|array|null, criteria?: { true?: EntryType, false?: EntryType } | null }`. OpenAPI requires only `type`; api.md's ParamField marks `instructions` **required**. **Disagreement flagged**: spec permits omitting/nulling instructions; docs prose says required. JS SDK builder `noul()` defaults instructions to `null` (`src/questions.ts`).
- Choice: `{ type: "choice", instructions?: EntryType, criteria: map<string, string|object|array|null> }` — criteria **required**; an option may map to `null` (undescribed). **Max 255 options per Choice** (api.md; corroborated by the launch blog: "Jev supports a cardinality up to 255. For the higher cardinality choices, we do a 2 stage-system of scoring independently then making an explicit choice" — https://typesafe.ai/blog/introducing-system-one-models-and-jev, 2026-09-15). **[observed]**
- Score: `{ type: "score", instructions?: EntryType, criteria: ordered array<string|object|array> }`. **Disagreement flagged**: api.md says "at least two levels; the API accepts up to 10"; OpenAPI `ScoreQuestion.criteria` has `minItems: 1` and **no maxItems**; JS SDK validates ≥2 client-side (`src/questions.ts::validateQuestions`) but has no 10 cap. Treat 2–10 as the documented safe range; 1 is technically spec-legal.

**Answer schemas** (all carry `type` echoing the question type; response envelope is `{ model, answers: map<id, Answer>, usage: { input_tokens: int, output_tokens: int } }`):
- Noul answer: `{ type: "noul", noul: number }` — "Probability of a yes answer or a true statement, from 0 to 1... values near 0.5 indicate uncertainty" (OpenAPI `NoulAnswer.noul`). **No `confidence` field on Noul** (confidence page: "Noul answers don't carry one"). The numeric field is called `noul`, not `p` or `probability`. **[observed]**
- Choice answer: `{ type: "choice", choice: string, confidence: number, probabilities: map<option, number> }` — "highest-probability option"; probabilities "floats that sum to approximately 1" (OpenAPI wording). **[observed]**
- Score answer: `{ type: "score", score: number, confidence: number, legend: map<string, EntryType>, probabilities: map<levelIndexString, number> }` — `score` is "the probability-weighted average of the rubric levels. May fall between integer levels"; legend/probabilities keys are level **indices as strings** (`"0"`, `"1"`, ...). **[observed]**
- `confidence` is 0–1, derived from the distribution shape. The confidence page's worked example computes Choice confidence as `(count·peak − 1)/(count − 1)`, i.e. normalized peak mass, and notes it's an approximation for 3 options (https://docs.typesafe.ai/confidence.md). **[observed as documented formula, not as the production implementation]**
- `model` in the response "reports the versioned ID that answered" (models page) — but the OpenAPI `SystemOneResponse.model` description says only "May differ from the alias supplied in the request" with example `"jev-latest"`. Log the raw value; docs say it should be a versioned ID like `jev-1.13.0`.

## Models, versions, aliases

Source: https://docs.typesafe.ai/models.md (2026-09-22).

- Current model: `jev-1.13.0`. `jev-latest` → `jev-1.13.0` ("most recent stable, official release"; SDK default). `jev-preview` → `jev-1.13.0`, with warning: "`jev-preview` currently points to the same model as `jev-latest`. There is no preview build available right now." **[observed]**
- Aliases move when a new release ships ("answers behind it can change without a change on your side"); first-party advice: if you tuned confidence thresholds against a version, **pin the versioned ID, not the alias**. **[actionable]**
- No version history table and no deprecation notices are published anywhere in the docs index. Version history beyond 1.13 could not be established (see Gaps).
- `GET /v1/models` returns `{ models: [{ name, description, release_date }] }`; it "currently lists the aliases"; versioned IDs are accepted regardless (models page). ModelMetadata example `release_date: "2026-09-15"` matches the public launch date in the blog. **[observed]**
- Jev is not fine-tuned or LoRA-adapted per account; trained with RLCD (RL for Calibrated Decisions); "the same weights serve every account" (models page). **[observed claim]**
- Language: English primary; CJK handled but less accurate; "test on your own content" (models page, Language support).

## Hard limits

Source: https://docs.typesafe.ai/models.md (2026-09-22).

- **Context**: "64k tokens per request; 32k tokens for `state` plus the longest question" — i.e., total budget covers state + all questions combined; the 32k check is state + the single longest question. This **confirms** the ~32k figure but the first-party wording is state+longest-question, not state alone. **[observed]**
- **Rate limits**: 250,000 tokens/second and 1,200 requests/minute for `jev-1.13`; over either → `429`. First-party warning (verbatim): "Rate limits are adjusting dynamically... the limits above can change without notice while we do... Higher limits are available on custom and enterprise plans. Contact sales@typesafe.ai." **[observed, but explicitly unstable]**
- **Max questions per call**: no published numeric cap. OpenAPI enforces only `minProperties: 1`. First-party cookbooks demonstrate large fan-outs (218 questions in one call — semantic_find cookbook; 450-pair decisions — entity_alignment cookbook), and the fan-out page says "adding more questions usually has little effect on response time" — bounded in practice by the 64k context budget. **[observed absence of a cap]**
- **Choice options**: max 255. **Score levels**: docs 2–10 (see disagreement above).
- **Timeouts**: no first-party server timeout published. SDK defaults are per-attempt 10s (JS `TypeSafeClientConfig.timeout`, `src/retry.ts::DEFAULT_TIMEOUT_MS = 10_000`). **Disagreement flagged within the Python SDK**: `typesafe_sdk.constants.DEFAULT_TIMEOUT = 10.0` (constants reference) but `RetryPolicy.timeout` defaults to `30.0` (retries reference) — the constants page and RetryPolicy page contradict each other. There is no total retry budget in either SDK.
- **Concurrency limits**: not published in any first-party source (searched docs index, api.md, models.md, llms.txt). Only the RPM limit (1,200/min) exists.

## Latency and pricing

- **Pricing**: `$42 / $0.042` per Btok/Mtok for `jev-1.13`; "Charged per input token. Output tokens are free" (models page). OpenAPI `Usage.output_tokens`: "Output tokens are currently free of charge." **[observed]** Cost therefore scales with **state size and question text** (all input), **not** with question count per se beyond tokens — but extra questions do use input tokens (skill page: "Extra questions still use tokens; measure actual request budgets"). A first-party cookbook measured batching 13 questions into one call as "12.2x cheaper and 10.0x faster" vs. 13 calls (parallel_questions cookbook). **[observed first-party measurement]**
- **No pricing page exists** at typesafe.ai/pricing (HTTP 404, retrieved 2026-09-22). Billing on the account side runs on **Credits** consumed per Input, not direct per-token invoices: MCA §8.2 — Credits expire "the earlier of the end of the Term and 12 months after purchase"; promotional credits (potentially free) are consumed before purchased credits; multi-account promo-credit farming is prohibited. **[observed]**
- **Latency**: "End-to-end response time is 70ms-500ms for TypeSafe" (launch blog, 2026-09-15). Nuance from the same post: "our published evals are generally run from our laptops on the West Coast (this is where our service is currently based)." Homepage demo shows one run at "$0.000081, Completed in 0.114s." **[claimed]** No p50/p99/percentile SLOs published anywhere first-party.
- **Relative claims**: "193.6x Faster, 444.6x Cheaper" (homepage, methodology in the blog: workflow evals vs. LLM reference models, self-acknowledged possible bias). Treat as **[claimed]**.
- **OpenRouter listing** (secondary, not first-party): "$0.042/M input tokens, $0/M output token, 32K context" — note the 32k context there matches the state+longest-question figure, not the 64k total; OpenRouter URL https://openrouter.ai/typesafe (retrieved via search snippet 2026-09-22). **[claimed, secondary]**

## Data handling

Sources: Privacy Policy https://typesafe.ai/legal/privacy-policy (last updated Nov 19, 2025); MCA https://typesafe.ai/legal/mca (last updated Sep 19, 2026); DPA https://typesafe.ai/legal/data-processing (last updated Apr 24, 2026); Legal index https://docs.typesafe.ai/legal.md. All retrieved 2026-09-22.

- **Training**: Privacy Policy, operative sentence: "We will not train or fine tune any artificial intelligence or machine learning models on your prompts or other Input." MCA §4.1: the license "does not grant TypeSafe the right to, and TypeSafe will not, include Customer Data in a dataset used to train (i.e., to modify the model weights of) any artificial intelligence or machine learning models without Customer's prior consent." Models page: "Jev is not trained on customer requests or responses." **[observed]**
- **Telemetry carve-out (important)**: MCA §4.1 grants a **perpetual** license for Customer Data "to derive and generate Telemetry, to monitor for fraud and abuse..., and as necessary to comply with applicable Laws," and §4.3 defines Telemetry ("technical logs, hashes, summary statistics and classifications, metrics, and learnings") which TypeSafe "may Process without restriction, including to improve the Services." So: no weight-training, but derived telemetry is unrestricted in perpetuity. **[actionable]** — quote this to anyone assuming "zero retention of anything."
- **Retention**: Privacy Policy: "We retain personal data about you for as long as reasonably necessary to provide you with the Services." MCA §10.3: "TypeSafe will be under no obligation to store or retain Customer Data and may delete Customer Data at any time in its sole discretion." No published numeric retention window for API Input. **[observed absence of a number]**
- **Zero data retention**: Legal index (https://docs.typesafe.ai/legal.md): "We also offer zero data retention (ZDR) for enterprise customers. Contact privacy@typesafe.ai to learn more." That is the entire published ZDR mechanism — no self-serve flag, no API parameter. **[observed]**
- **Regions**: Privacy Policy, International Visitors: "The Services are hosted in the United States ('U.S.')... you are transferring your personal data outside of those regions to the U.S. for storage and processing." DPA covers EU SCCs (Module 2/3, Irish courts/law) and UK Addendum; supervisory authority for EEA = Ireland. **[observed]**
- **Subprocessors**: DPA §3.1 points to https://trust.typesafe.ai/subprocessors; the trust center is a Vanta-hosted SPA whose subprocessor list requires JS (we could not extract the list from static HTML — noted as a retrieval gap, not an absence of the page).
- **DPA obligations**: security-incident notice "within 72 hours"; customer audit at most once per 12 months; breach notice obligations per SCCs. **[observed]**
- **Terms-of-use restrictions relevant to us**: MCA §2.3(b) prohibits using Output "to perform model distillation, train a model to imitate the output of the Services, or develop... a similar or competing product or service." If we train downstream classical models on Jev probabilities (as the TypeSafe autoresearch cookbook suggests), that is arguably distinct from imitating the service, but flag it. **[actionable]**
- The docs marketing sentence "Jev is not trained on customer requests or responses" (models page) matches the legal text; no disagreement found between marketing and terms on training. The gap is retention: marketing says nothing; the MCA says TypeSafe may delete at any time and telemetry is unrestricted.

## Error semantics and retryability

Sources: api.md §Errors; JS SDK `src/retry.ts`, `src/errors.ts`, `src/client.ts` (tag v0.6.0); Python SDK retries/constants pages.

- Published statuses (api.md table): `401` invalid key; `422` request validation (body details the offending field; OpenAPI `HTTPValidationError` with `detail[].loc/msg/type/input`); `429` rate limit ("Back off and retry after a short delay"); `529` overloaded ("Retry after a short delay"). **[observed]**
- **Disagreement flagged**: docs publish only 401/422/429/529, but the first-party SDK maps and classifies more: `400 BadRequestError`, `401 AuthenticationError`, `403 PermissionDeniedError`, `404 NotFoundError`, `422 UnprocessableEntityError`, `429 RateLimitError`, `≥500 InternalServerError` (`src/errors.ts::APIError.fromResponse`). 529 is handled as a 5xx by the SDK. Client code should expect 400/403/404 even though api.md doesn't list them.
- **Retryable statuses (SDK default, both SDKs)**: `408, 429, and 500–599` (RetryPolicy docs and `DEFAULT_RETRY_POLICY.httpStatuses` in `src/retry.ts`). This makes **529 retryable**. **Non-retryable**: 400, 401, 403, 404, 422 (unless the server says otherwise), and `APIUserAbortError`. **[actionable]** — our client treating all HTTP status errors as non-retryable diverges from first-party guidance.
- **Retry mechanics (JS SDK defaults, `DEFAULT_RETRY_POLICY`)**: `maxRetries: 2`, `backoffInitialMs: 500` doubling to `backoffMaxMs: 5000`, `backoffJitter: 0.25`, `respectRetryAfter: true` honoring `retry-after-ms` (preferred) and `Retry-After` up to `maxRetryAfterMs: 60000`, retries on connection errors and timeouts. Python mirrors with same defaults (seconds; `RetryPolicy.timeout` default 30.0 — see timeout disagreement above).
- **Headers**: request ID surfaced from `x-typesafe-request-id` (JS SDK `requestIdFrom`; Python `error.request_id`). Rate-limit responses carry `Retry-After` (docs say SDKs honor it) and the SDK also parses `retry-after-ms`. Retried JS SDK requests add `X-TypeSafe-Retry-Count`. Log `request_id` for support escalations. **[observed]**
- What a client should do, per first-party guidance: on 429/529 "retry the request with exponential backoff instead of retrying immediately"; SDKs do this automatically with default policy (api.md §Handling rate limits).

## First-party guidance on question wording, calibration, thresholds

Sources: primitives pages, confidence page, jaggedness page (last reviewed 2026-09-17), all retrieved 2026-09-22.

- **Wording**: ask one narrow snap judgment per question ("the kind of judgment a highly knowledgeable person could make in a few seconds"); question IDs are not sent to the model, so `instructions` must carry the complete meaning; reference state via backticked paths like `ticket.messages[0].text`; `instructions` and criteria may be structured objects/arrays. (primitives.md; api.md.)
- **Literal reading** (jaggedness #1): Jev answers the question you wrote, not meant; "Where interpretation is unavoidable, split it into two literal questions and combine them in code." **[actionable]** for guard-question authoring.
- **Calibration/thresholds** (confidence page): three-range pattern (act / proceed-with-caution / don't-act); thresholds scale with risk (example: `confidence < 0.5` → human; `> 0.9` for destructive ops); "Start with conservative thresholds, test with your own data." Also: a confidence measure is provided but not privileged — "you are never locked into our definition... which is exactly why we give you the full `probabilities`." **[actionable]**
- **Noul has no confidence**; 0.5 means equal yes/no probability, not medium intensity; use one Noul per label when several may apply (skill + primitives + models pages).
- **Structural invariants are not guaranteed** (jaggedness #8, with first-party measured examples): `noul` vs. `probabilities["yes"]` of the same question disagreed (0.22 vs. 0.01); `refund` + `not_refund` nouls summed to 1.19. "Don't carry a threshold tuned on a Noul over to a Choice, and don't hold the model to arithmetic identities between separate questions." **[actionable]** — relevant to any `stuck`/guard logic that combines noul complements.
- **Context rot**: accuracy falls as state grows with irrelevant detail; filter first in code, or use a relevance Noul (jaggedness #5 + classifying_rag_passages cookbook). **[actionable]** for how much conversation we ship per guard call.
- **Known 1.13 weaknesses**: no reliable counting, no numeric interpolation between Score levels ("do not use score outputs to compute the exact magnitude"), dates read as text, adversarial state content "can move the answer" — "State is data, and jev-1.13 does not treat it as hostile by default." **[actionable]** for a guard layer evaluating attacker-controlled text.
- **Confidence ≠ workflow correctness**: "Choice/Score confidence summarizes distribution concentration, not overall workflow correctness or permission to act" (skill page). A full first-party agent skill exists at https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md (linked from quickstart).

## SDK status (for choosing what to trust)

- JS SDK `@typesafe-ai/sdk` v0.6.0 (npm, published 2026-09-15; provenance-attested GitHub Actions build from `typesafe-ai/typesafe-sdk-js`), MIT, Node ≥20. Changelog: only v0.5.7 (2026-09-11, initial) and v0.6.0 (2026-09-15, breaking: Score criteria as ordered sequence). **[observed]**
- Python `typesafe-sdk` 0.7.1 (PyPI, 2026-09-21; maintainer Daniel Gafni). History: 0.0.1a0 (2026-09-09), 0.5.7 (2026-09-14), 0.6.0 (2026-09-15, Score criteria sequence), 0.7.0 (2026-09-18, msgspec→pydantic, adds `response_model`), 0.7.1 (2026-09-21, early API-key validation). **[observed]**
- Python SDK supports OpenRouter (`~typesafe/jev-latest` via `https://openrouter.ai/api`) and Vercel AI Gateway (`https://ai-gateway.vercel.sh/typesafe`, model `typesafe-ai/jev`) as first-party-configured alternates; "This requires the alternative API to follow the TypeSafe OpenAPI spec" (usage page). **[observed]**
- Python SDK supports `extra_body` for forward-compatible fields; example field `beam_width` is explicitly "illustrative; only send fields supported by the API" — **no `beam_width` field is documented in the OpenAPI spec**. Do not send it. **[observed]**

## Status page

- Live status page exists: https://status.typesafe.ai (RSS: https://status.typesafe.ai/feed). Recent incidents retrieved 2026-09-22: "API issues — intermittent downtime and system instability" (2026-09-21 23:40 UTC, open at retrieval) and "Console is unavailable" (2026-09-21 08:16, resolved). **[observed]** — service stability is currently rough; retry logic matters.

## Gaps / not found

Searched: full docs index (llms.txt), api.md, models.md, legal index + all three legal documents, trust center, status page feed, npm/PyPI registry metadata and JS SDK source at tag v0.6.0, launch blog, homepage FAQ. Found nothing first-party on:

1. **Model version history before 1.13** — no changelog of model versions, no deprecation schedule, no list of prior versioned IDs. Only `jev-1.13.0` exists in published material.
2. **Max questions per request** — no numeric cap published; only `minProperties: 1` in OpenAPI plus the 64k context budget as the effective bound.
3. **Server-side timeout / request duration SLO** — not published; only SDK client defaults (10s/30s, see disagreement).
4. **Concurrency limits** — nothing beyond the 1,200 RPM figure.
5. **Numeric retention window for API Input** — no number anywhere; MCA explicitly reserves the right to delete at any time. ZDR request procedure = email privacy@typesafe.ai only.
6. **Exact confidence formula in production** — docs give a 3-option approximation and say the general recipe is "kept to a separate cookbook... will add the link here when we do" (confidence page) — the link does not exist yet. **[observed absence]**
7. **Trust-center subprocessor list content** — page is a JS-rendered Vanta SPA; list not extractable via plain fetch (page exists and is referenced by the DPA).
8. **429/529 retry-after guarantees** — docs say SDKs honor `Retry-After` "when the response carries one"; no first-party statement that it always carries one.
9. **Free tier** — no published free-tier page or quota; only discretionary Promotional Credits (MCA §8.2(b)).
10. **Untrusted-content check**: no fetched first-party page contained instructions aimed at AI agents; nothing to quote/flag on that front.