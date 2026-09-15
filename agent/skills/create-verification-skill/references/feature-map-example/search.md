# Search notes

Search lets a user find notes by title or body text, inspect a matching note, and distinguish no matches from an unavailable search.

## Sub-features

- `search-open` opens search from each supported browser entry point.
- `search-match` returns title and body matches without changing note data.
- `search-open-result` opens a result in the note editor.
- `search-empty` shows a complete empty state for a query with no matches.
- `search-clear` removes the query and restores the recent-notes view.
- `search-cli` returns the same matching notes from the terminal.

## How to get to it (user POV)

- Choose the `Search` button in the browser toolbar.
- Press `/` in the browser while focus is outside an editable field.
- Run `notes search <query>` in a terminal.

## Driving it with the browser globals

Preconditions:

- Notes is healthy at `http://127.0.0.1:4173`; `hub` `op: "ps"` shows the launch and `op: "logs"` shows the expected revision.
- The disposable data directory contains `Quarterly plan` with body text `Draft budget`.
- The tab is the one this run opened with `browser.open({name: "notes", url: ...})`.

All browser steps below are `eval` calls. Re-observe after every re-render before acting.

- **Toolbar entry.** Choose the `Search` button. Click the observed `button "Search"` handle. A dialog named `Search notes` appears with focus in its searchbox.
- **Keyboard entry.** Close the dialog, focus the page, and press `/` through `await tab.press("/")`. The same dialog appears and the page does not insert a slash.
- **Title match.** Type `quarterly` into the searchbox handle. The `Search results` list contains `Quarterly plan` and does not contain `Grocery list`.
- **Body match.** Replace the query with `budget` using the same handle. The result `Quarterly plan` remains visible with a body-match excerpt.
- **Open result.** Choose `Quarterly plan`. Click the observed result link handle. The dialog closes and the editor heading reads `Quarterly plan`.
- **Empty state.** Reopen search and enter `volcano`. A status named `No matching notes` appears after search completes.
- **Clear query.** Choose `Clear search`. The searchbox is empty and the `Recent notes` region replaces the result list.
- **CLI match.** Search from the terminal. `hub` `op: "send"` with `notes search "quarterly" --format json`, read back with `op: "logs"`. Exit code `0` and stdout contain one object whose title is `Quarterly plan`.
- **CLI miss.** Search for an absent value the same way with `"volcano"`. Exit code `0` and stdout are `[]`.
- **Proof.** Capture the populated result state. `await tab.ariaSnapshot()` and `await tab.screenshot()`; both artifacts identify Notes, the query, and `Quarterly plan`.

## Gotchas

- Pressing `/` while the editor or searchbox has focus inserts text instead of opening search.
- Results update after a short debounce. `await tab.waitForSelector(...)` on the results list or the empty status, not a fixed sleep.
- Archived notes are excluded unless the user enables `Include archived`.
- The CLI defaults to human-readable output. Use `--format json` for stable assertions.
- Opening a result changes browser state. Reopen search before proving another query.
- Handles die on re-render; re-observe rather than reusing an id from an earlier step.
