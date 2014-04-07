# Under consideration

Define a unified restricted format for metadata:

 * in Evernote.tmLanguage
 * in markdown2
 * in sublime_evernote

When view shows a note:

- Diff local note with online version (approx on the markdown!)

## Highlighting invalid tags/attributes

Example: `<style>...<div id="...">` would mark them as invalid.
However this requires copying the Markdown language modifying only some parts.
Not very modular. Enough?

## Event Listeners

### On Load

- Parse metadata, set flag to signal this is a note
- If `download_on_load` redownload
