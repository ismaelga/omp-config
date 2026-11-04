---
name: alchemy-cli
description: Use when working with Alchemy balances, token/NFT holdings, transfer history, prices, transactions/receipts/logs/blocks, contract reads, simulation, JSON-RPC, webhooks, or apps.
---

# Alchemy CLI

`alchemy` replaces Alchemy MCP. Check `alchemy --json --no-interactive config status`; if unauthenticated, tell the user to run `alchemy auth login` themselves.

## Quick reference

Always pass global `--json --no-interactive` (before the command) and parse JSON stdout on success or JSON stderr on failure.

| Need | Command |
|---|---|
| Native balance | `alchemy --json --no-interactive evm data balance <address> -n <network>` |
| ERC-20 balances + metadata | `alchemy --json --no-interactive evm data tokens balances <address> --metadata -n <network>` |
| Owned NFTs | `alchemy --json --no-interactive evm data nfts <address> -n <network>` |
| Transfer history | `alchemy --json --no-interactive evm data history <address> --from-block <block> --to-block <block> -n <network>` |
| Spot price | `alchemy --json --no-interactive evm data price symbol ETH,USDC -n <network>` |
| Transaction / receipt | `alchemy --json --no-interactive evm tx <hash> -n <network>` / `alchemy --json --no-interactive evm receipt <hash> -n <network>` |
| Logs (topic filter) | `alchemy --json --no-interactive evm logs --address <address> --topic <topic0> --from-block <block> --to-block <block> -n <network>` |
| Block | `alchemy --json --no-interactive evm block <number> -n <network>` |
| Contract view | `alchemy --json --no-interactive evm contract read <address> 'balanceOf(address)(uint256)' --args '["<owner>"]' -n <network>` |
| Simulate asset changes | `alchemy --json --no-interactive evm simulate asset-changes --tx '{"to":"<address>","from":"<address>","data":"0x...","value":"0x0"}' -n <network>` |
| Raw JSON-RPC | `alchemy --json --no-interactive evm rpc eth_getBalance "<address>" "latest" -n <network>` (params are positional JSON values, one per argument) |
| Networks | `alchemy --json --no-interactive evm network list` (`-n`/`--network` selects a network for EVM queries) |
| Webhooks | `alchemy --json --no-interactive webhook list` |
| Apps | `alchemy --json --no-interactive app list` |

## Writes and discovery

Never run without explicit user instruction: native/ERC-20 sends, state-changing contract calls, approvals, swap execution, cross-chain bridge execution, Solana sends/delegation, x402 requests that pay, wallet connect/use/disconnect, webhook create/update/delete, app and allowlist administration writes, and gas-manager policy writes. Prefer read-only simulation, swap quote, `--estimate`, or `--dry-run` before an authorized action; previews do not authorize execution.

Discover commands with `alchemy --json --no-interactive agent-prompt` and `alchemy help <command...>`. Trust installed help over memory. EVM data needs an API key; admin surfaces may need Alchemy login.

## Output and pitfalls

Success JSON is on stdout; errors JSON on stderr. Unauthenticated `evm gas -n base-mainnet` returned `AUTH_REQUIRED`, exit 3. `agent-prompt` requires both global flags. Use `--metadata`, `evm data history`, `evm receipt`, `evm logs --topic`, `evm contract read`, and `evm simulate asset-changes --tx`; these are not top-level commands. Contract signatures include input/output types, e.g. `balanceOf(address)(uint256)`. `evm rpc` has no `--params` flag.