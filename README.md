SublimeEvernote
===============

[Sublime Text 3](http://www.sublimetext.com/3) plugin for [Evernote](http://www.evernote.com)

This package combines [jamiesun](https://github.com/jamiesun)'s original plugin with [rekotan](https://github.com/rekotan)'s update. Jamiesun's original package doesn't work for me because it attempts to authenticate via the (now) outdated Userstore.authenticate. Rekotan updated the package to use a proper token; however, the update also sends the markdown as preformatted text. I prefer to transform the Markdown to Evernote rich text, and if you're of the same mind, then this is your Sublime-Evernote package.

I did little work here--merely cobbling together the efforts of the original pacakge and a fork.

# Installation

clone this repository with

```sh
$ git clone --recursive http://github.com/timlockridge/SublimeEvernote.git
```

in

* Windows: `%APPDATA%/Roaming/Sublime Text 3/Packages/`
* OSX: `~/Library/Application Support/Sublime Text 3/Packages/`
* Linux: `~/.Sublime Text 3/Packages/`
* Portable Installation: `Sublime Text 3/Data/`

# Usage

**Note: When you first run this package from the command palette, it will launch a browser window with your Evernote developer token. Copy the token and paste it into the prompt at the bottom of your Sublime window. Sublime will store the token data in `Sublime Text 3/Packages/User/SublimeEvernote.sublime-settings`**

`Command Palette` > `Send to evernote`

`Context menu` > `Send to Evernote`

`Context menu` > `Evernote settings`

# Some Modifications

This version will work in Sublime Text 3 with Python 3, and it will also allow you to choose which
notebook you would like to save your note to.
