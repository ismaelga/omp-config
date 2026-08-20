---
description: Compress a natural-language memory file into caveman format to cut input tokens
---
Compress the file at: $ARGUMENTS

Tool lives outside the auto-loaded skill surface so it costs nothing per turn.
Read `~/.omp/agent/tools/caveman-compress/SKILL.md` for the full compression and
preservation rules, then run from that directory:

```bash
cd ~/.omp/agent/tools/caveman-compress && python3 -m scripts <absolute_filepath>
```

The CLI detects the file type, compresses, validates, and cherry-picks fixes on
validation errors (max 2 retries). Original is backed up as `FILE.original.md`
before overwrite; on repeated failure the original is left untouched.

Only prose files (`.md`, `.txt`, `.typ`, `.tex`, extensionless). Never source,
config, or lockfiles. Code blocks, inline backticks, URLs, paths, commands,
versions, and frontmatter are copied byte-exact.
