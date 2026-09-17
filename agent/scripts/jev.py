#!/usr/bin/env python3
"""jev.py — Jev (TypeSafe System One) decision layer for omp routing and guarding.

First-level classifier standing between an agent and three decisions:

  route  — which subagent / skill / MCP server fits a task text
  guard  — does an outgoing operation leak content, go off-scope, or destroy state
  ask    — raw escape hatch for arbitrary typed judgments

Advisory by default: `route` always exits 0 and callers fall back to boring
defaults on low confidence or failure. `guard` is the exception — it blocks:
exit 0 clear, 1 flagged (escalate to user), 2 API failure (treated as flagged).

Requires TYPESAFE_API_KEY in the environment (already exported in omp shells).
Content passed to `guard --content` transits api.typesafe.ai; that is a
deliberate user decision (2026-09-17), documented here so it is not re-litigated
silently.

Catalogs are read from disk at call time, not hardcoded:
  agents: task.disabledAgents (config.yml) defines what NOT to offer
  skills: agent/skills/*/SKILL.md frontmatter name+description
  mcp:    agent/mcp.json server objects
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
AGENT_DIR = Path(os.environ.get("JEV_AGENT_DIR", str(Path.home() / ".omp" / "agent")))
GUARD_THRESHOLD = 0.5  # any hazard probability at/above this flags the op

DEFAULT_AGENTS = {
    "scout": "Fast read-only codebase research and broad pattern searches. Returns compressed context, never edits.",
    "reviewer": "Code review specialist for quality analysis of a concrete changeset or diff.",
    "security-reviewer": "Read-only security specialist for evidence-backed vulnerability discovery in code.",
    "task": "General-purpose agent with full capabilities for delegated multi-step implementation work.",
    "none": "No subagent needed; the main session should handle this directly.",
}

MCP_SERVERS = {
    "linear": "Linear issue tracker: projects, issues, cycles, comments, releases, diffs, documents.",
    "sentry": "Sentry error tracking: production issues, events, stack traces, release health.",
    "kpk": "Documentation Q&A and search for KPK docs.",
}


def load_agent_catalog() -> dict[str, str]:
    """Active agents from DEFAULT_AGENTS minus task.disabledAgents in config.yml."""
    disabled: set[str] = set()
    cfg = AGENT_DIR / "config.yml"
    if cfg.exists():
        text = cfg.read_text()
        m = re.search(r"^task:\n(?:[ \t]+\S.*\n)*?[ \t]+disabledAgents:\n((?:[ \t]+-[ \t]*\S.*\n?)+)", text, re.M)
        if m:
            disabled = {ln.strip().lstrip("- ").strip() for ln in m.group(1).splitlines() if ln.strip()}
    return {k: v for k, v in DEFAULT_AGENTS.items() if k not in disabled}


def load_skill_catalog() -> dict[str, str]:
    """Skill name -> one-line description from SKILL.md frontmatter."""
    catalog: dict[str, str] = {}
    skills_dir = AGENT_DIR / "skills"
    if not skills_dir.is_dir():
        return catalog
    for md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            text = md.read_text()
        except OSError:
            continue
        m = re.search(r"^name:\s*(.+)$", text, re.M)
        d = re.search(r"^description:\s*(>?-?)\s*(.+)\n((?:[ \t]+[^\n]*\n)*)", text, re.M)
        if not m:
            continue
        name = m.group(1).strip().strip("\"'")
        if not d:
            catalog[name] = f"skill {name}"
            continue
        # Folded (>) and multi-line values: capture indented continuation lines.
        folded = d.group(2).strip("\"'") + " ".join(
            ln.strip() for ln in d.group(3).splitlines() if ln.strip()
        )
        folded = folded.strip()
        desc = (folded if folded else d.group(2).strip("\"'").strip()) or f"skill {name}"
        catalog[name] = desc
    return catalog


def load_mcp_catalog() -> dict[str, str]:
    """Enabled MCP servers from mcp.json: name -> inferred one-line description."""
    catalog: dict[str, str] = {}
    mcp_file = AGENT_DIR / "mcp.json"
    if not mcp_file.exists():
        return MCP_SERVERS
    try:
        data = json.loads(mcp_file.read_text())
    except (OSError, json.JSONDecodeError):
        return MCP_SERVERS
    servers = data.get("mcpServers", data) if isinstance(data, dict) else {}
    for name, obj in servers.items():
        if not isinstance(obj, dict) or obj.get("disabled") is True or obj.get("enabled") is False:
            continue
        catalog[name] = MCP_SERVERS.get(name, f"MCP server {name}")
    return catalog or MCP_SERVERS


def evaluate(state, questions: dict) -> dict:
    """POST to System One; return answers map. Raises on HTTP/network error."""
    payload = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    return body["answers"]


def cmd_route(args) -> int:
    catalogs = {
        "agents": load_agent_catalog(),
        "skills": load_skill_catalog(),
        "mcp": load_mcp_catalog(),
    }
    if args.catalog:
        catalogs = {k: v for k, v in catalogs.items() if k in args.catalog}
    if not catalogs:
        print(json.dumps({"error": "no catalogs selected or found"}))
        return 2

    # One request, all independent questions in parallel — Jev sees the full
    # catalog text; we ask per-catalog Choice plus speculative Noul questions.
    state = {"task": args.item, "catalogs": catalogs}
    questions: dict = {}
    for cat, entries in catalogs.items():
        if not entries:
            continue
        questions[f"pick_{cat}"] = {
            "type": "choice",
            "instructions": f"Which {cat} entry best fits this task? Pick 'none' if nothing fits.",
            "criteria": {**{k: v for k, v in entries.items()}, "none": "No entry fits this task."},
        }
    questions["needs_isolation"] = {
        "type": "noul",
        "instructions": "Would this task benefit from running in an isolated git worktree, separate from the current workspace?",
    }
    questions["security_sensitive"] = {
        "type": "noul",
        "instructions": "Does this task touch secrets, credentials, authentication, or other security-sensitive material?",
    }

    try:
        answers = evaluate(state, questions)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        # Advisory: never block dispatch on classifier failure.
        print(json.dumps({"error": f"jev route failed: {e}", "fallback": "task"}))
        return 0

    result = {"agents": {}, "skills": {}, "mcp": {}}
    for cat, entries in catalogs.items():
        key = f"pick_{cat}"
        if key not in answers:
            continue
        a = answers[key]
        probs = a.get("probabilities", {})
        ranked = sorted(
            ((k, p) for k, p in probs.items() if k in entries),
            key=lambda kv: kv[1],
            reverse=True,
        )
        result[cat] = {
            "best": a.get("choice"),
            "confidence": a.get("confidence"),
            "top3": [{"name": k, "p": round(p, 3)} for k, p in ranked[:3]],
        }
    result["needs_isolation"] = answers.get("needs_isolation", {}).get("noul")
    result["security_sensitive"] = answers.get("security_sensitive", {}).get("noul")
    print(json.dumps(result))
    return 0


def cmd_guard(args) -> int:
    state = {
        "operation": args.op,
        "destination": args.target or "",
        "paths": [p.strip() for p in (args.paths or "").split(",") if p.strip()],
        "content": args.content or "",
        "note": args.note or "",
    }
    questions = {
        "exfiltrates": {
            "type": "noul",
            "instructions": "Does this operation send repository content, credentials, or user data to an external destination (API, webhook, email, third-party service, paste site) that is not its obvious intended recipient?",
            "criteria": {
                "true": "Repo content, secrets, tokens, or user data goes somewhere external beyond the operation's legitimate purpose",
                "false": "Nothing leaves the machine, or the destination is the obvious intended one (e.g. git push to the project's own remote)",
            },
        },
        "off_scope": {
            "type": "noul",
            "instructions": "Is this operation beyond what a user plausibly asked for — an action the user would be surprised to find happened?",
            "criteria": {
                "true": "The operation clearly exceeds any plausible user request (e.g. deleting unrelated data, changing unrelated config, posting somewhere unasked)",
                "false": "The operation is a normal part of fulfilling a user request",
            },
        },
        "destructive": {
            "type": "noul",
            "instructions": "Is this operation irreversible or destructive such that git or local backups cannot undo it (e.g. force-push, deleting remote state, wiping untracked files, purging external systems)?",
            "criteria": {
                "true": "Effect cannot be recovered via git or local means; external or deleted state is gone",
                "false": "Recoverable: local edits, committed changes, or operations git can undo",
            },
        },
    }

    try:
        answers = evaluate(state, questions)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        # Fail closed: unreachable classifier = treat op as flagged.
        print(json.dumps({"verdict": "flagged", "reason": f"jev guard failed (fail-closed): {e}"}))
        return 2

    hazards = {k: round(a.get("noul", 1.0), 3) for k, a in answers.items()}
    flagged = [k for k, p in hazards.items() if p >= GUARD_THRESHOLD]
    verdict = "flagged" if flagged else "clear"
    print(json.dumps({"verdict": verdict, "hazards": hazards, "flagged": flagged}))
    return 1 if flagged else 0


def cmd_ask(args) -> int:
    state = json.loads(args.state)
    questions = json.loads(args.questions)
    try:
        answers = evaluate(state, questions)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        print(json.dumps({"error": f"jev ask failed: {e}"}))
        return 2
    print(json.dumps(answers))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Jev (TypeSafe) routing and guard decisions for omp.")
    p.add_argument("--agent-dir", help="omp agent config dir (default ~/.omp/agent)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("route", help="Classify a task text against agent/skill/MCP catalogs.")
    pr.add_argument("--item", required=True, help="Task text to classify.")
    pr.add_argument("--catalog", action="append", choices=["agents", "skills", "mcp"], help="Restrict to these catalogs (repeatable). Default: all.")
    pr.set_defaults(func=cmd_route)

    pg = sub.add_parser("guard", help="Hazard-check an outgoing operation (blocking).")
    pg.add_argument("--op", required=True, help="Operation type, e.g. push, deploy, mcp-write, external-send.")
    pg.add_argument("--target", help="Destination of the operation.")
    pg.add_argument("--paths", help="Comma-separated file paths involved.")
    pg.add_argument("--content", help="Content/command text being sent (transits api.typesafe.ai).")
    pg.add_argument("--note", help="Context: what the user asked for.")
    pg.set_defaults(func=cmd_guard)

    pa = sub.add_parser("ask", help="Raw typed judgments: state + questions JSON.")
    pa.add_argument("--state", required=True, help="JSON state value.")
    pa.add_argument("--questions", required=True, help="JSON questions map.")
    pa.set_defaults(func=cmd_ask)

    args = p.parse_args()
    if args.agent_dir:
        os.environ["JEV_AGENT_DIR"] = args.agent_dir
    if not os.environ.get("TYPESAFE_API_KEY"):
        print(json.dumps({"error": "TYPESAFE_API_KEY not set"}), file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())