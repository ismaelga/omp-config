#!/usr/bin/env bash
# Removes local branches (and their worktrees and origin branches) whose GitHub PR is merged.
# Dry run by default; pass --apply to delete. Usage: prune-merged-branches.sh [--apply] [repo-dir...]
#
# A branch is kept when: it is main/master/release/*, any PR from it is still open, no PR from it
# merged, its worktree has uncommitted or untracked files, or it holds commits the merged PR head
# does not (work done after the merge). Squash merges are why this asks GitHub instead of using
# `git branch --merged`.
set -euo pipefail

apply=0
if [[ "${1:-}" == "--apply" ]]; then apply=1; shift; fi
repos=("$@")
if [[ ${#repos[@]} -eq 0 ]]; then
  repos=(~/karpatkey/code/vault-ethsigner ~/karpatkey/code/steward ~/karpatkey/code/kpk-devops)
fi

for repo in "${repos[@]}"; do
  cd "$repo"
  slug="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
  echo "== $slug"
  git fetch -q --prune origin
  git worktree prune

  # macOS ships bash 3.2 (no associative arrays): look the branch's worktree up in the listing.
  listing="$(git worktree list --porcelain)"
  worktree_of() {
    awk -v want="branch refs/heads/$1" '/^worktree /{p=substr($0, 10)} $0 == want {print p}' <<<"$listing"
  }

  while IFS= read -r br; do
    case "$br" in main | master | release/*) continue ;; esac
    prs="$(gh pr list -R "$slug" --head "$br" --state all --limit 20 --json state,headRefOid,mergedAt)"
    if [[ "$(jq '[.[] | select(.state == "OPEN")] | length' <<<"$prs")" != 0 ]]; then
      echo "keep  $br (open PR)"; continue
    fi
    head="$(jq -r '[.[] | select(.state == "MERGED")] | sort_by(.mergedAt) | last | .headRefOid // empty' <<<"$prs")"
    if [[ -z "$head" ]]; then echo "keep  $br (no merged PR)"; continue; fi
    tip="$(git rev-parse "refs/heads/$br")"
    if [[ "$tip" != "$head" ]] && ! { git cat-file -e "$head^{commit}" 2>/dev/null && git merge-base --is-ancestor "$tip" "$head"; }; then
      echo "keep  $br (commits after the merged PR head)"; continue
    fi
    tree="$(worktree_of "$br")"
    if [[ -n "$tree" && -n "$(git -C "$tree" status --porcelain)" ]]; then
      echo "keep  $br (dirty worktree $tree)"; continue
    fi
    remote=0
    git show-ref -q --verify "refs/remotes/origin/$br" && remote=1
    echo "prune $br${tree:+ worktree=$tree}$([[ $remote == 1 ]] && echo ' +origin')"
    if [[ $apply == 1 ]]; then
      [[ -n "$tree" ]] && git worktree remove "$tree"
      git branch -q -D "$br"
      [[ $remote == 1 ]] && git push -q origin --delete "$br"
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads/)
done
