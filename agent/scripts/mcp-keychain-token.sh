#!/usr/bin/env bash
#
# Print "Bearer <token>" for an MCP server whose credential lives in the macOS
# login keychain. Used from mcp.json as:
#
#   "headers": { "Authorization": "!$HOME/.omp/agent/scripts/mcp-keychain-token.sh omp/notion-mcp-token" }
#
# Measured 2026-09-01, and it decides how this is wired: configuring an
# Authorization header at all suppresses omp's managed OAuth credential for that
# URL, and a failing header command does NOT hand the credential back. Sentry
# with a keychain header and no stored item did not mount; the same entry with
# the header removed returned its org. So a server carries this header only once
# its keychain item exists -- mcp-credentials-wizard.sh adds the header at the
# moment it stores the token, and the two stay in lockstep.
#
# Exiting non-zero on a missing item therefore buys a clear error rather than a
# fallback: it stops the obvious inline form,
# `printf 'Bearer %s' "$(security find-generic-password ...)"`, from exiting 0
# with an empty token and putting a literal "Bearer " on the wire.
#
# No `-A` on the keychain item: `security add-generic-password` grants the
# `security` binary itself access, and `security` is also the reader here, so
# reads succeed unprompted without widening the ACL to every process.

set -euo pipefail

service="${1:?usage: mcp-keychain-token.sh <keychain-service-name> [account]}"
account="${2:-omp}"

token=$(security find-generic-password -w -s "$service" -a "$account" 2>/dev/null) || {
	printf 'no keychain item for service=%s account=%s\n' "$service" "$account" >&2
	exit 1
}

[[ -n $token ]] || {
	printf 'keychain item service=%s account=%s is empty\n' "$service" "$account" >&2
	exit 1
}

printf 'Bearer %s' "$token"
