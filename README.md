Evernote for Sublime Text
=========================

[Sublime Text](http://www.sublimetext.com/3) plugin for [Evernote](http://www.evernote.com)

This package is based on [SublimeEvernote](https://github.com/jamiesun/SublimeEvernote).
It adds support for Sublime Text 3 (thanks to [timlockridge](https://github.com/timlockridge/SublimeEvernote)) and includes new features as open/update of notes from Sublime.

**NB:** this plugin has only been tested in Sublime Text 3

# Main Features

 * **Send a note to Evernote:** converts the markdown document in the current view into rich text and sends it to your Evernote. You will be able to choose a title, tags and the notebook where to store it.
 * **Open a note from Evernote**: shows panels to choose a note from a notebook, converts it to markdown and presents it in a view.
 * **Update note**: when editing the markdown of an opened note you can save it back to Evernote (again in rich text).
 * **Full two-way metadata support**: you can set and change the note's title, notebook and tag just by providing a YAML metadata header in your markdown source.

# Installation

Clone this repository with

```sh
$ git clone --recursive http://github.com/bordaigorl/sublime-evernote.git
```

in

* Windows: `%APPDATA%/Roaming/Sublime Text 3/Packages/`
* OSX: `~/Library/Application Support/Sublime Text 3/Packages/`
* Linux: `~/.Sublime Text 3/Packages/`
* Portable Installation: `Sublime Text 3/Data/`

# Usage

## First use

When you first run this package from the command palette, it will launch a browser window with your Evernote developer token. Copy the token and paste it into the prompt at the bottom of your Sublime window. Sublime will store the token data in `Sublime Text 3/Packages/User/SublimeEvernote.sublime-settings`.

If you need to reconfigure the plugin go to `Preferences > Package Settings > Evernote` and select `Reconfigure Authorisation` or goto

`Command Palette` > `Evernote: Reconfigure`

## Commands

### Send to Evernote

`Command Palette` > `Evernote: Send to Evernote`

This will create a new note containing the HTML version of the markdown code of your active view.
You will be able to specify the title, tags and notebook either from panels or with a metadata block ([see below](#metadata))

### Open Note

`Command Palette` > `Evernote: Open Evernote Note`

This will open a panel from which you can select a notebook and a note in it.
The selected note will be converted in markdown format and opened in a view.
This command only handles the main contents of the note and ignores the attachments.

### Update Note

`Command Palette` > `Evernote: Update Evernote Note`

or `ctrl+s` on views displaying an Evernote note.

When the current view is associated with an Evernote note (maybe because you just sent it to Evernote or because it is an opened note) you can update the note with this command.
The [metadata](#metadata) will be updated according to the metadata block and attachments stored in the original Evernote note will be left alone.


## Metadata

A markdown source can start with a metadata block like the following:

```yaml
---
title: My Note's Title
tags: misc, sublime
notebook: My Notebook 
---
```

When sending or updating the note, the plugin will extract this metadata and set/change it accordingly. When such header is incomplete or missing, when sending the note to Evernote the plugin will ask for input for the missing fields.

The `tags` field can be an unquoted list or a json list such as `["my long tag", "tag2"]`.

# Acknowledgements

 * Original Plugin: [jamiesun](https://github.com/jamiesun/SublimeEvernote)
 * Port to ST3:
     - [rekotan](https://github.com/rekotan/SublimeEvernote)
     - [timlockridge](https://github.com/timlockridge/SublimeEvernote)
 * Markdown2 converter: [trentm](https://github.com/trentm/python-markdown2/)
 * HTML2Markdown: [Aaron Swartz](https://github.com/aaronsw/html2text)
 * Evernote API: <https://github.com/evernote/evernote-sdk-python>