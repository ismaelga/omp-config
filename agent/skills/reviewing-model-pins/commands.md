# Verification commands

Verbatim and runnable. Each answers one question. Replace model selectors as needed.

## Provider health: what can answer at all

Run this first. Quota and credit state appear in no catalog.

```bash
omp usage                                   # per-account plan limits and reset times
KEY=$(omp token openrouter | tr -d '\n\r ')
curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY"
curl -s https://openrouter.ai/api/v1/key     -H "Authorization: Bearer $KEY"
```

`total_usage` at or above `total_credits` does not fail everything: OpenRouter refuses
on a request's *estimated* max cost, so probes at a few hundred `max_tokens` answer 200
while the long reasoning generations a role actually issues return HTTP 402 "requires
more credits, or fewer max_tokens". Probe at realistic output length, not with a
one-word prompt. `omp usage` reports the plan-based providers: a row at 100% is a role
already walking its chain.

A provider that fails under `omp bench` is not necessarily unreachable — bench takes
its own path. Confirm through the session path before calling a route dead:

```bash
cd /tmp && omp -p --no-session --no-tools --no-skills --no-extensions \
  --model openai-codex/gpt-6-astra --thinking high "Reply with exactly: OK"
```

## Catalog: what exists, on which provider, with what capabilities

```bash
omp models refresh                       # re-fetch every authenticated provider's catalog
omp models                               # everything, grouped by provider
omp models zai                           # one provider (ACTION is positional; --provider does not exist)
omp models find astra                    # substring search across providers
omp models --json > /tmp/omp-models.json # machine-readable: contextWindow, maxTokens, thinking, input, cost
```

The JSON is the honest source for capability facts. Fields per row: `provider`, `id`,
`selector`, `contextWindow`, `maxTokens`, `thinking` (the effort ladder actually
served), `input` (modalities — check for `image`), `cost`.

Diff catalog against pins in one pass:

```bash
python3 - <<'PY'
import json, re, yaml, pathlib
cat = {m["selector"] for m in json.load(open("/tmp/omp-models.json"))["models"]}
cfg = pathlib.Path.home() / ".omp/agent/config.yml"
src = cfg.read_text()
refs = set(re.findall(r'(?m)^\s*(?:-\s*|[a-z]+:\s*)((?:[a-z0-9-]+/)+[a-zA-Z0-9._:-]+)', src))
for r in sorted(refs):
    base = r.split(":")[0] if not r.endswith(("*",)) else r
    if "*" in r: continue
    if base not in cat and r not in cat:
        print("NOT IN CATALOG:", r)
PY
```

Chain keys and wildcards (`ollama-cloud/*`, `default`) are not models — expect them in
the output and ignore them.

## Prices and live availability

The catalog can carry a stale price. A live provider call cannot.

```bash
curl -s https://openrouter.ai/api/v1/models | python3 -c '
import json,sys,datetime
d=json.load(sys.stdin)["data"]
want={"google/gemini-3.8-flash","z-ai/glm-5.3-flash"}
for m in d:
    if m["id"] in want:
        p=m["pricing"]
        print(f"{m[\"id\"]:32s} in={float(p[\"prompt\"])*1e6:7.3f} out={float(p[\"completion\"])*1e6:7.3f} "
              f"cr={float(p.get(\"input_cache_read\") or 0)*1e6:6.3f} ctx={m.get(\"context_length\")} "
              f"created={datetime.date.fromtimestamp(m[\"created\"])}")'
```

`created` dates a model's arrival on that route. Interactive price is the `prompt` /
`completion` pair — a `:batch` selector at half the price is the batch API, not a
discount on ordinary calls.

```bash
curl -s --max-time 20 https://ollama.com/api/tags | jq -r '.models[].name' | sort
curl -s --max-time 15 -o /dev/null -w '%{http_code}\n' https://ollama.com/library/glm-5.3-flash
curl -s --max-time 20 https://models.dev/api.json -o /tmp/modelsdev.json   # cross-check, API-tier biased
```

models.dev reports the API tier. Subscription/plan tiers are lower — never quote it for
a plan-routed model.

## Modality: prove image input on the exact route

The catalog's `input` list is vendor metadata. Before a vision role lands on a
route, send it a picture whose answer you know.

```bash
python3 - <<'PY'
import base64, json, struct, urllib.request, zlib
def chunk(t, d):
    c = t + d
    return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
row = b"\x00\xff\x00\x00\xff\x00\x00"                       # one 2px red row, filter byte 0
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(row * 2)) + chunk(b"IEND", b""))
key = open("/tmp/.ol.key").read().strip()                    # omp token ollama-cloud
body = {"model": "glm-5.3-flash", "stream": False, "think": "low",
        "messages": [{"role": "user", "content": "What color is this image? One word.",
                      "images": [base64.b64encode(png).decode()]}]}
req = urllib.request.Request("https://ollama.com/api/chat", data=json.dumps(body).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=180) as r:
    print(json.load(r)["message"]["content"][:120])
PY
```

"Red" is a pass. An HTTP 400, an empty answer, or a description of nothing means the
route does not really take images however the catalog is marked.

## Local measurements: what this machine actually got

`model_perf` is every real session call, not a synthetic benchmark. n≥50 is meaningful.

```bash
sqlite3 -header -column ~/.omp/agent/agent.db "
  select model_key, cast(samples as int) n,
         round(output_tokens/(gen_ms/1000.0),1) tok_s,
         round(ttft_ms/ttft_samples) ttft_ms
  from model_perf where samples >= 10 order by tok_s desc;"
```

```bash
sqlite3 -header -column ~/.omp/agent/agent.db "
  select provider, credential_type, coalesce(disabled_cause,'-') from auth_credentials order by provider;"
sqlite3 -header -column ~/.omp/agent/agent.db "
  select provider, sum(cost) spend, min(date(created_at/1000,'unixepoch')) from usage_cost_history group by provider;"
```

Reading a WAL database read-only shows empty tables. Either use the commands above
(read-write handle) or copy `agent.db`, `agent.db-wal`, `agent.db-shm` to a temp dir and
open the copy.

## Latency and throughput: `omp bench`

```bash
cd /tmp && omp bench openrouter/google/gemini-3.8-flash ollama-cloud/glm-5.3:high ollama-cloud/gpt-oss:120b \
  --profile chat --runs 5 --par 2 --max-tokens 256
```

Reports TTFT p50/p95, tok/s, cost per run. Profiles: `chat`, `prefill`, `generation`,
`prompt-cache`. Keep `--max-tokens` capped or a verbose model's wall time swamps the
TTFT signal you came for.

Raw wire timing, no harness in the path:

```bash
KEY=$(omp token openrouter | tr -d '\n\r ')
for i in 1 2 3; do
  curl -s -o /tmp/or.json -w '%{time_total}\n' https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
    -d '{"model":"google/gemini-3.8-flash","messages":[{"role":"user","content":"Reply with exactly: OK"}],"reasoning":{"effort":"low"}}'
done
```

## Fallback link audit

Every link, one cheap call each. Dead hops answer 410 (retired) or 403 (region-gated).

```bash
cd /tmp && omp bench <every-link-selector-without-effort-suffix> --profile chat --runs 1 --max-tokens 32 --par 6
```

## Bakeoff: execution-scored coding comparison

The shape that decided the `task` pin. Write it to a **file** and run it as a
background `bash` job — never `omp -p` fan-out (concurrent CLI processes deadlock) and
never a long eval cell (the kernel can die mid-run and take every raw output with it,
which is exactly how one pass lost 18 scored calls).

1. Pick 2 problems shaped like the harness's own work (a unified-diff generator, a glob
   matcher — both small, both with brutal edge cases).
2. Write a validator that **executes** the returned code: apply the diff back and demand
   exact reconstruction, check hunk arithmetic, context bounds, minimality against
   `difflib`; run the glob matcher over a fixed case table.
3. **Validate the validator** before scoring anyone: a reference implementation must pass
   it (fixed cases plus randomized trials), and the case table itself must be checked
   against an implementation you did not write. For glob, `git check-ignore` is that
   second opinion — it is on every machine and implements the same `*`/`**`/`[]` rules:

   ```bash
   git init -q /tmp/globcheck && git -C /tmp/globcheck config core.ignorecase false
   printf '/%s\n' "$PATTERN" > /tmp/globcheck/.gitignore
   git -C /tmp/globcheck check-ignore --no-index -q -- "$PATH_UNDER_TEST"; echo $?  # 0 = match
   ```

   Anchor the pattern with a leading `/` (gitignore matches bare patterns at any depth),
   force `core.ignorecase false` (APFS defaults it true and every `[a-z]` case will
   disagree), and expect one class of false positive: git also ignores children of an
   ignored directory, so `/*` "matches" `a/b`.
4. Call each provider directly over HTTP with the credential from `auth_credentials`
   (`https://ollama.com/api/chat` with `"think": "<level>"`, or the OpenRouter
   completions endpoint), 2–3 samples per model per problem, 6 workers.
5. **Append every finished call to a JSONL as it lands**, raw response text included.
   A run that only writes at the end is unobservable while it runs and unsalvageable if
   it dies, and keeping the text means a spec fix can be re-scored without re-billing
   the models -- but only for calls that completed. An infra-failed call (timeout,
   HTTP 500, empty 200) has a row and no text, so re-scoring it is a fresh call at
   fresh cost. Append the row before writing the text, or a write that throws costs
   you the whole record: a model id containing `/` did exactly that here, killing a
   run mid-flight on a path that did not exist.
   Progress of a silent job: `lsof -p <pid> -a -i -nP | grep -c ESTABLISHED`.
6. Record: pass count, wall time, output tokens (verbosity is a latency cost), and
   whether reasoning mode returned code at all.

## Config validation after editing

```bash
python3 -c "import yaml; yaml.safe_load(open('$HOME/.omp/agent/config.yml')); print('yaml ok')"
cd ~/.omp/agent && grep -vE '^\s*(#|$)' <(git show HEAD:config.yml) > /tmp/a.yml \
  && grep -vE '^\s*(#|$)' config.yml > /tmp/b.yml && diff /tmp/a.yml /tmp/b.yml
```

The comment-stripped diff proves which settings actually changed when a pass rewrites
large comment blocks. Then confirm a selector resolves where intended:

```bash
cd /tmp && omp -p --no-session --no-tools --no-skills --model anthropic/claude-fable-5-1 "Reply with exactly: OK"
```

Resolution is what this proves. Its wall time is not route latency — CLI startup
dominates.
