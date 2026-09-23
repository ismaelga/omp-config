---
description: Never wipe the filesystem root or home directory, or rewrite published git history
# Regex net behind config.yml's bash.patterns denies, which are exact-match and
# cover bash only. This matches the shapes they miss (sudo/env//bin prefixes,
# any rm flag order or case, trailing / or /*, redirect suffixes, force flags
# after other push arguments) in bash AND eval, which bash.patterns never sees.
# It interrupts the stream before the call runs, but it is not a deny: with
# ttsr.repeatMode `once` it fires once per session.
# Patterns read the raw JSON tool arguments, so quotes may arrive as \" and
# newlines as a literal \n; the delimiter classes allow for both.
condition:
  # rm with any flags whose target is /, ~, $HOME, ${HOME}, optionally quoted,
  # with an optional trailing / or /*. `/tmp/x`, `~/build`, `./` do not match.
  - '(?:^|[\s;&|(`"''=]|\\n)(?:(?:sudo|doas)(?:\s+-\S+)*\s+|env\s+|command\s+|exec\s+|xargs\s+)*(?:/usr)?(?:/bin/)?rm(?:\s+-{1,2}[\w-]+)+(?:\s+[^\s;&|"''`\\-][^\s;&|"''`\\]*)*\s+\\?["'']?(?:/|~|\$\{?HOME\}?)/?\*?\\?["'']?(?=$|[\s;&|)`"''\\])'
  # git push with bare --force, -f (alone or bundled), or a +refspec.
  # --force-with-lease passes: agents use it after rebasing feature branches.
  - '\bgit(?:\s+-C\s+\S+)?\s+push\b[^;&|\\`\n]*?\s(?:--force|-[a-zA-Z]*f[a-zA-Z]*|\+[\w./-]+(?::\S*)?)(?=$|[\s;&|)`"''\\])'
  - '\bgit\s+filter-branch\b'
  # eval-native recursive deletes of home or root (Python shutil, Node/Bun fs).
  - '\b(?:rmtree|rmSync|rm)\(\s*(?:(?:pathlib\.)?Path\.home\(\)|os\.homedir\(\)|homedir\(\)|process\.env\.HOME|Bun\.env\.HOME|os\.environ\[\s*\\?["'']HOME\\?["'']\s*\]|os\.getenv\(\s*\\?["'']HOME\\?["'']\s*\)|os\.path\.expanduser\(\s*\\?["'']~/?\\?["'']\s*\)|\\?["''](?:/|~/?)\\?["''])\s*[,)]'
scope: "tool:bash, tool:eval"
---
This call would delete the filesystem root or the home directory, or rewrite published git history. Do not run it, and do not rephrase it to get past this stop. If a removal was intended, target the exact subdirectory by name. If the user explicitly asked for a force push or a history rewrite, stop and ask them to run it themselves.
