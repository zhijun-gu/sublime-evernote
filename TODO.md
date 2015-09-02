# Release Checklist

 * update `EVERNOTE_PLUGIN_VERSION`
 * check `DEBUG` is `False`
 * update Changelog in Readme
 * add update message to `messages` and `messages.json`
 * update Contributors in Readme if needed
 * update wiki if needed
 * add release on GitHub with release notes from Readme

# Features

 * New note: `templates = find_resources("EvernoteNewNote*.sublime-snippet")`
   If `len(templates)==1` use that. Otherwise show quick panel.
   If `template` argument is given pass that verbatim to `insert_snippet`
   (so possible args can be `{"name": snippet_file}` or `{"contents": snippet}`)
 * Global style

# Documentation

 * Known bugs in wiki:
     - paragraphs and spacing #71, #67
     - proxy
 * More notes on issues in Readme
 * See [issues with `needs-docs` label](https://github.com/bordaigorl/sublime-evernote/labels/needs-docs)

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
