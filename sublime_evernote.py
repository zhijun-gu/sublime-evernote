#coding:utf-8
import sys
import os

# The differences in what is required between Sublime Text 2 and Sublime Text 3 should
# be clear enough from the "if sys.version_info" blocks in the code. Specifically
#   -- there are some syntax changes between Python 2 and 3
#   -- Python 3 uses unicode strings by default, and some values had to be converted from bytes
#   -- the Python 3 evernote API is invoked differently, and needs a username in order to
#          build a noteStore URL.
# Also, OAuth was not implemented, because the Python 3 that is built into Sublime Text 3 was
# built without SSL. So, among other things, this means no http.client.HTTPSRemoteConnection
#
# Finally, as another TODO, the __get_notebooks() function should probably employ some kind
# of caching, but, alas, it is getting late here . . .
#
# One gotcha -- the THttpClient.py file, included in the Evernote Python 3 SDK, includes
# a call to .iteritems() on a dictionary on line 138. This is forbidden in python 3. I
# fixed it by changing .iteritems() to .items() and submitted an Issue on GitHub, so
# hopefully this will be fixed (10/02/2013)

# Make sure that we have absolute path names for the libraries that we wat to import, and
# import the correct version of the Evernote SDK, depending on whether we are using
# SublimeText2/Python2 or SublimeText3/Python3

package_file = os.path.normpath(os.path.abspath(__file__))
package_path = os.path.dirname(package_file)
lib_path = os.path.join(package_path, "lib")

if sys.version_info.major == 2:
    evernote_path = os.path.join(package_path, "lib", "evernote-sdk-python", "lib")
if sys.version_info.major == 3:
    evernote_path = os.path.join(package_path, "lib", "evernote-sdk-python3", "lib")

if lib_path not in sys.path:
    sys.path.append(lib_path)
if evernote_path not in sys.path:
    sys.path.append(evernote_path)

import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

if sys.version_info.major == 2:
    from evernote.api.client import EvernoteClient
if sys.version_info.major == 3:
    import evernote.edam.userstore.UserStore as UserStore
    import evernote.edam.notestore.NoteStore as NoteStore
    import thrift.protocol.TBinaryProtocol as TBinaryProtocol
    import thrift.transport.THttpClient as THttpClient

import sublime
import sublime_plugin
import webbrowser
import markdown2


def LOG(*args):
    print("Evernote: ", *args)

USER_AGENT = {'User-Agent': 'SublimeEvernote/2.0'}

EVERNOTE_SETTINGS = "Evernote.sublime-settings"


# Top level calls to sublime are ignored in Sublime Text 3 at startup!
# settings = sublime.load_settings(EVERNOTE_SETTINGS)


class SendToEvernoteCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        self.view = view
        self.window = sublime.active_window()
        self.settings = sublime.load_settings(EVERNOTE_SETTINGS)

    def to_markdown_html(self):
        region = sublime.Region(0, self.view.size())
        encoding = self.view.encoding()
        if encoding == 'Undefined':
            encoding = 'utf-8'
        elif encoding == 'Western (Windows 1252)':
            encoding = 'windows-1252'
        contents = self.view.substr(region)
        markdown_html = markdown2.markdown(contents, extras=['footnotes', 'fenced-code-blocks', 'codehilite', 'cuddled-lists', 'code-friendly', 'metadata'])
        return markdown_html


    def connect(self, callback, **kwargs):
        sublime.status_message("initializing..., please wait...")

        def __connect(token, noteStoreUrl):
            LOG("token param {0}".format(token))
            LOG("url param {0}".format(noteStoreUrl))
            LOG("token pre {0}".format(self.settings.get("token")))
            LOG("url pre {0}".format(self.settings.get("noteStoreUrl")))
            self.settings.set("token", token)
            self.settings.set("noteStoreUrl", noteStoreUrl)
            LOG("Token {0}".format(self.settings.get(token)))
            LOG("url {0}".format(self.settings.get(noteStoreUrl)))
            sublime.save_settings(EVERNOTE_SETTINGS)
            LOG("post Token {0}".format(self.settings.get(token)))
            LOG("post url {0}".format(self.settings.get(noteStoreUrl)))
            callback(**kwargs)

        def __derive_note_store_url(token):
            token_parts = token.split(":")
            id = token_parts[0][2:]
            url = "http://www.evernote.com/shard/" + id + "/notestore"
            return url

        def on_token(token):
            noteStoreUrl = self.settings.get("noteStoreUrl")
            if (sys.version_info.major == 3) and (not noteStoreUrl):
                 noteStoreUrl = __derive_note_store_url(token)
            __connect(token, noteStoreUrl)

        token = self.settings.get("token")
        if token:
            noteStoreUrl = self.settings.get("noteStoreUrl")
            if not noteStoreUrl:
                noteStoreUrl = __derive_note_store_url(token)
                __connect(token, noteStoreUrl)
        else:
            webbrowser.open_new_tab("https://www.evernote.com/api/DeveloperToken.action")
            self.window.show_input_panel("Developer Token (required):", "", on_token, None, None)

    def send_note(self, **kwargs):
        token = self.settings.get("token")

        if sys.version_info.major == 2:
            noteStore = EvernoteClient(token=token, sandbox=False).get_note_store()
        if sys.version_info.major == 3:
            noteStoreUrl = self.settings.get("noteStoreUrl")
            LOG("I've got this for noteStoreUrl -->{0}<--".format(noteStoreUrl))
            LOG("I've got this for token -->{0}<--".format(token))
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
            noteStoreHttpClient.setCustomHeaders(USER_AGENT)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)

        markdown_html = self.to_markdown_html()

        def __send_note(title, notebookGuid, tags):

            note = Types.Note()

            if sys.version_info.major == 2:
                note.title = title.encode('utf-8')
            if sys.version_info.major == 3:
                note.title = title

            note.content = '<?xml version="1.0" encoding="UTF-8"?>'
            note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
            note.content += '<en-note>'

            if sys.version_info.major == 2:
                note.content += markdown_html.encode('utf-8')
            if sys.version_info.major == 3:
                note.content += markdown_html

            note.content += '</en-note>'

            note.notebookGuid = notebookGuid
            note.tagNames = tags and tags.split(",") or []

            try:
                sublime.status_message("Posting note, please wait...")
                if sys.version_info.major == 2:
                    cnote = noteStore.createNote(note)
                if sys.version_info.major == 3:
                    cnote = noteStore.createNote(token, note)
                sublime.status_message("Successfully posted note: guid:%s" % cnote.guid)
            except Errors.EDAMUserException as e:
                args = dict(title=title, notebookGuid=notebookGuid, tags=tags)
                if e.errorCode == 9:
                    self.connect(self. send_note, **args)
                else:
                    if sublime.ok_cancel_dialog('Error %s! retry?' % e):
                        self.connect(self.send_note, **args)
            except Exception as e:
                sublime.error_message('Error %s' % e)

        def __get_notebooks():
            notebooks = None
            try:
                sublime.status_message("Fetching notebooks, please wait...")
                if sys.version_info.major == 2:
                    notebooks = noteStore.listNotebooks()
                if sys.version_info.major == 3:
                    notebooks = noteStore.listNotebooks(token)
                sublime.status_message("Fetched all notebooks!")
            except Exception as e:
                sublime.error_message('Error getting notebooks: %s' % e)
            return notebooks

        notebooks = __get_notebooks()
        def on_title(title):
            def on_tags(tags):
                def on_notebook(notebook):
                    __send_note(title, notebooks[notebook].guid, tags)
                self.window.show_quick_panel([notebook.name for notebook in notebooks], on_notebook)
            self.window.show_input_panel("Tags (Optional):", "", on_tags, None, None)

        if not kwargs.get("title"):
            self.window.show_input_panel("Title (required):", "", on_title, None, None)
        else:
            __send_note(kwargs.get("title"), kwargs.get("notebookGuid"), kwargs.get("tags"))


    def run(self, edit):
        if not self.settings.get("token"):
            self.connect(self.send_note)
        else:
            self.send_note()


class OpenEvernoteNoteCommand(sublime_plugin.WindowCommand):

    def __init__(self, window):
        self.window = window
        self.settings = sublime.load_settings(EVERNOTE_SETTINGS)

    def run(self):
        from html2text import html2text

        token = self.settings.get("token")

        # TODO: refactor pop out in def
        if sys.version_info.major == 2:
            noteStore = EvernoteClient(token=token, sandbox=False).get_note_store()
        if sys.version_info.major == 3:
            noteStoreUrl = self.settings.get("noteStoreUrl")
            LOG("I've got this for noteStoreUrl -->{0}<--".format(noteStoreUrl))
            LOG("I've got this for token -->{0}<--".format(token))
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
            noteStoreHttpClient.setCustomHeaders(USER_AGENT)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)

        # TODO: refactor, join with __get_notebooks and caching (with reset after timeout)
        notebooks = None
        try:
            sublime.status_message("Fetching notebooks, please wait...")
            if sys.version_info.major == 2:
                notebooks = noteStore.listNotebooks()
            if sys.version_info.major == 3:
                notebooks = noteStore.listNotebooks(token)
            sublime.status_message("Fetched all notebooks!")
        except Exception as e:
            sublime.error_message('Error getting notebooks: %s' % e)

        def on_notebook(notebook):
            nid = notebooks[notebook].guid
            notes = noteStore.findNotesMetadata(
                token, NoteStore.NoteFilter(notebookGuid=nid),
                0,
                100,
                NoteStore.NotesMetadataResultSpec(includeTitle=True)).notes
            def on_note(i):
                note = noteStore.getNote(token, notes[i].guid, True, False, False, False)
                newview = self.window.new_file()
                newview.set_scratch(True)
                newview.set_name(note.title)
                mdtxt = html2text(note.content)
                newview.settings().set("auto_indent", False)
                newview.settings().set("$evernote_guid", note.guid)
                newview.run_command("insert", {"characters": mdtxt})
                syntax = newview.settings().get("md_syntax", "Packages/Markdown/Markdown.tmLanguage")
                newview.set_syntax_file(syntax)
                newview.show(0)
                # LOG(mdtxt)

            sublime.set_timeout(lambda: self.window.show_quick_panel([note.title for note in notes], on_note), 0)
        self.window.show_quick_panel([notebook.name for notebook in notebooks], on_notebook)

