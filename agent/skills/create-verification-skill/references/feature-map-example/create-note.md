# Create a note

Create note lets a user save a titled note from the browser or CLI, cancel an unfinished draft, and confirm the saved note from a second user-facing view.

## Sub-features

- `create-open` opens a blank editor from each browser entry point.
- `create-save` persists a title and body.
- `create-cancel` discards an unfinished browser draft.
- `create-cli` creates the same note shape from the terminal.

## How to get to it (user POV)

- Choose the `New note` button in the browser toolbar.
- Press `n` in the browser while focus is outside an editable field.
- Run `notes create --title <title> --body <body>` in a terminal.

## Driving it with the browser globals

Preconditions:

- Notes is healthy at `http://127.0.0.1:4173`; `hub` `op: "ps"` shows the launch and `op: "logs"` shows the expected revision.
- No note is titled `Release checklist`.
- The disposable data directory is the one this run started.

All browser steps below are `eval` calls against the tab opened with `browser.open({name: "notes", url: "http://127.0.0.1:4173"})`. Re-observe after every navigation or re-render, then act in the same cell.

- **Open editor.** Choose `New note`. Run `await tab.ariaSnapshot()` to find the `button "New note"` handle, then click it. A form named `Note editor` appears with focus in the `Title` textbox.
- **Enter content.** Type the title and body. `await tab.ref("e5").fill("Release checklist")` on the `Title` textbox handle, then the same on the `Body` textbox handle. The `Save note` button becomes enabled.
- **Save note.** Choose `Save note`. Click the observed `Save note` button handle. A status named `Note saved` appears and the heading reads `Release checklist`.
- **Confirm persistence.** Return to the note list and reopen the note. Click `All notes`, re-observe, click the `Release checklist` link. The editor shows both saved values.
- **Cancel draft.** Open a new note, enter `Discard me`, and choose `Cancel`. The note list returns and has no `Discard me` link.
- **CLI entry.** Create a second note. Send `notes create --title "CLI note" --body "Created from terminal" --format json` to the CLI session with `hub` `op: "send"` and read it back with `op: "logs"`. Exit code `0` and stdout contain the new note ID and title.
- **Proof.** Reopen both saved notes from `All notes`. Run `await tab.ariaSnapshot()` and `await tab.screenshot()`; `screenshot()` returns the path it wrote under `browser.screenshotDir`. The artifacts show `Release checklist` and `CLI note`.

## Gotchas

- Pressing `n` while a textbox has focus types the character instead of opening a new editor.
- Titles are trimmed on save. Assert the rendered title, not the draft input value.
- A save status alone is insufficient proof. Reopen the note from the list.
- Handles from `observe()` and `ariaSnapshot()` die on navigation or re-render; re-observe before clicking.
- Remove `Release checklist` and `CLI note` during fixture cleanup, but retain their proof artifacts.
