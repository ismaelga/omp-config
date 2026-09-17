"""Catalog loaders: agents, skills, MCP servers, read live from disk.

Nothing hardcoded to drift: agents respect config.yml task.disabledAgents,
skills come from SKILL.md frontmatter, MCP servers from mcp.json enabled
state.
"""

import json
import os
import re
from pathlib import Path

AGENT_DIR = Path(os.environ.get("JEV_AGENT_DIR", str(Path.home() / ".omp" / "agent")))

DEFAULT_AGENTS = {
    "scout": "Fast read-only codebase research and broad pattern searches. Returns compressed context, never edits.",
    "reviewer": "Code review specialist for quality analysis of a concrete changeset or diff.",
    "security-reviewer": "Read-only security specialist for evidence-backed vulnerability discovery in code.",
    "interrogator": "Read-only adversarial reviewer: reviews a changeset against a fixed prompt and rubric, returns evidence-cited findings only.",
    "task": "General-purpose agent with full capabilities for delegated multi-step implementation work.",
    "none": "No subagent needed; the main session should handle this directly.",
}

MCP_SERVERS = {
    "linear": "Linear issue tracker: projects, issues, cycles, comments, releases, diffs, documents.",
    "sentry": "Sentry error tracking: production issues, events, stack traces, release health.",
    "kpk": "Documentation Q&A and search for KPK docs.",
    "voyager": "MCP server voyager.",
    "cloudflare": "Cloudflare MCP server.",
    "slack": "Slack MCP server.",
}


def load_agent_catalog() -> dict[str, str]:
    """Active agents from DEFAULT_AGENTS minus task.disabledAgents in config.yml."""
    disabled: set[str] = set()
    cfg = AGENT_DIR / "config.yml"
    if cfg.exists():
        text = cfg.read_text()
        m = re.search(
            r"^task:\n(?:[ \t]+\S.*\n)*?[ \t]+disabledAgents:\n((?:[ \t]+-[ \t]*\S.*\n?)+)",
            text,
            re.M,
        )
        if m:
            disabled = {ln.strip().lstrip("- ").strip() for ln in m.group(1).splitlines() if ln.strip()}
    return {k: v for k, v in DEFAULT_AGENTS.items() if k not in disabled}


def load_skill_catalog() -> dict[str, str]:
    """Skill name -> one-line description from SKILL.md frontmatter.

    Handles folded (`>`) and multi-line description values; continuation
    lines are captured, not truncated.
    """
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
        d = re.search(r"^description:\s*(>+|-+)?\s*(.*)\n((?:[ \t]+[^\n]*\n)*)", text, re.M)
        if not m:
            continue
        name = m.group(1).strip().strip("\"'")
        if not d:
            catalog[name] = f"skill {name}"
            continue
        first = d.group(2).strip().strip("\"'")
        cont = " ".join(ln.strip() for ln in d.group(3).splitlines() if ln.strip())
        desc = (first + " " + cont).strip() if cont else first
        catalog[name] = desc or f"skill {name}"
    return catalog


def load_mcp_catalog() -> dict[str, str]:
    """Enabled MCP servers from mcp.json: name -> one-line description.

    Fallback to MCP_SERVERS static if mcp.json is missing/unparseable/empty.
    """
    catalog: dict[str, str] = {}
    mcp_file = AGENT_DIR / "mcp.json"
    if not mcp_file.exists():
        return MCP_SERVERS
    try:
        data = json.loads(mcp_file.read_text())
    except (OSError, json.JSONDecodeError):
        return MCP_SERVERS
    servers = data.get("mcpServers", data) if isinstance(data, dict) else {}
    disabled_names = data.get("disabledServers", []) if isinstance(data, dict) else []
    for name, obj in servers.items():
        if name in disabled_names:
            continue
        if not isinstance(obj, dict) or obj.get("disabled") is True or obj.get("enabled") is False:
            continue
        catalog[name] = MCP_SERVERS.get(name, f"MCP server {name}")
    return catalog or MCP_SERVERS