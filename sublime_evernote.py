#coding:utf-8
import sys
import os
import json

# The differences in what is required between Sublime Text 2 and Sublime Text 3 should
# be clear enough from the "if sys.version_info" blocks in the code. Specifically
#   -- there are some syntax changes between Python 2 and 3
#   -- Python 3 uses unicode strings by default, and some values had to be converted from bytes
#   -- the Python 3 evernote API is invoked differently, and needs a username in order to
#          build a noteStore URL.
# Also, OAuth was not implemented, because the Python 3 that is built into Sublime Text 3 was
# built without SSL. So, among other things, this means no http.client.HTTPSRemoteConnection
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

PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3

if PY2:
    evernote_path = os.path.join(package_path, "lib", "evernote-sdk-python", "lib")
else:
    evernote_path = os.path.join(package_path, "lib", "evernote-sdk-python3", "lib")

if lib_path not in sys.path:
    sys.path.append(lib_path)
if evernote_path not in sys.path:
    sys.path.append(evernote_path)

import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

if PY2:
    from evernote.api.client import EvernoteClient
else:
    import evernote.edam.userstore.UserStore as UserStore
    import evernote.edam.notestore.NoteStore as NoteStore
    import thrift.protocol.TBinaryProtocol as TBinaryProtocol
    import thrift.transport.THttpClient as THttpClient

import sublime
import sublime_plugin
import webbrowser
import markdown2

ST3 = int(sublime.version()) >= 3000


def LOG(*args):
    print("Evernote: ", *args)

USER_AGENT = {'User-Agent': 'SublimeEvernote/2.0'}

EVERNOTE_SETTINGS = "Evernote.sublime-settings"

if PY2:
    def enc(txt):
        return txt.encode('utf-8')
else:
    def enc(txt):
        return txt

MD_EXTRAS = {
    'footnotes'          : None,
    'fenced-code-blocks' : None,
    'cuddled-lists'      : None,
    'code-friendly'      : None,
    'metadata'           : None,
    # This should be loaded from settings!
    'inline-css'         : {
        'pre': "color: #000000; font-family: monospace,monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; background-color: #f8f8f8; border: 1px solid #cccccc; border-radius: 3px 3px 3px 3px; overflow: auto; padding: 6px 10px; margin-bottom: 10px;",
        'code': "color: black; font-family: monospace,monospace; font-size: 0.9em;"
    }
}


def extractTags(tags):
    try:
        tags = json.loads(tags)
    except:
        tags = [t.strip(' \t') for t in tags and tags.split(",") or []]
    return tags


def populate_note(note, view, notebooks=[]):
    if view:
        contents = view.substr(sublime.Region(0, view.size()))
        body = markdown2.markdown(contents, extras=MD_EXTRAS)
        meta = body.metadata or {}
        body = enc(body)
        content = '<?xml version="1.0" encoding="UTF-8"?>'
        content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        content += '<en-note>'
        content += body
        content += '</en-note>'
        note.title = meta.get("title", note.title)
        tags = meta.get("tags", note.tagNames)
        if tags is not None:
            tags = extractTags(tags)
        LOG(tags)
        note.tagNames = tags
        note.content = content
        if "notebook" in meta:
            for nb in notebooks:
                if nb.name == meta["notebook"]:
                    note.notebookGuid = nb.guid
                    break
    return note

if ST3:
    def append_to_view(view, text):
        view.run_command('append', {
            'characters': text,
        })
        return view
else:
    def append_to_view(view, text):
        new_edit = view.begin_edit()
        view.insert(new_edit, view.size(), text)
        view.end_edit(new_edit)
        return view


class EvernoteDo():

    _noteStore = None
    _notebooks = None

    def token(self):
        return self.settings.get("token")

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
            if PY3 and (not noteStoreUrl):
                noteStoreUrl = __derive_note_store_url(token)
            __connect(token, noteStoreUrl)

        token = self.token()
        if token:
            noteStoreUrl = self.settings.get("noteStoreUrl")
            if not noteStoreUrl:
                noteStoreUrl = __derive_note_store_url(token)
                __connect(token, noteStoreUrl)
        else:
            webbrowser.open_new_tab("https://www.evernote.com/api/DeveloperToken.action")
            self.window.show_input_panel("Developer Token (required):", "", on_token, None, None)

    def get_note_store(self):
        if EvernoteDo._noteStore:
            return EvernoteDo._noteStore
        if PY2:
            noteStore = EvernoteClient(token=self.token(), sandbox=False).get_note_store()
        else:
            noteStoreUrl = self.settings.get("noteStoreUrl")
            LOG("I've got this for noteStoreUrl -->{0}<--".format(noteStoreUrl))
            LOG("I've got this for token -->{0}<--".format(self.token()))
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
            noteStoreHttpClient.setCustomHeaders(USER_AGENT)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)
        EvernoteDo._noteStore = noteStore
        return noteStore

    def get_notebooks(self):
        if EvernoteDo._notebooks:
            LOG("Using cached notebooks list")
            return EvernoteDo._notebooks
        notebooks = None
        try:
            noteStore = self.get_note_store()
            sublime.status_message("Fetching notebooks, please wait...")
            if PY2:
                notebooks = noteStore.listNotebooks()
            else:
                notebooks = noteStore.listNotebooks(self.token())
            sublime.status_message("Fetched all notebooks!")
        except Exception as e:
            sublime.error_message('Error getting notebooks: %s' % e)
        EvernoteDo._notebooks = notebooks
        return notebooks


class EvernoteDoText(EvernoteDo, sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        self.window = sublime.active_window()
        self.settings = sublime.load_settings(EVERNOTE_SETTINGS)
        if not self.token():
            self.connect(lambda **kw: self.do_run(edit, **kw), **kwargs)
        else:
            self.do_run(edit, **kwargs)


class EvernoteDoWindow(EvernoteDo, sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        # self.window = sublime.active_window()
        self.settings = sublime.load_settings(EVERNOTE_SETTINGS)
        if not self.token():
            self.connect(self.do_run, **kwargs)
        else:
            self.do_run(**kwargs)


class SendToEvernoteCommand(EvernoteDoText):

    def do_run(self, edit, **kwargs):
        self.do_send(**kwargs)

    def do_send(self, **args):
        noteStore = self.get_note_store()
        note = Types.Note()

        default_tags = args.get("default_tags", "")

        if "title" in args:
            note.title = args["title"]
        if "notebookGuid" in args:
            note.notebookGuid = args["notebookGuid"]
        if "tags" in args:
            note.tagNames = extractTags(tags)

        notebooks = self.get_notebooks()
        populate_note(note, self.view, notebooks)

        def on_cancel():
            sublime.status_message("Note not sent.")

        def choose_title():
            if not note.title:
                self.window.show_input_panel("Title (required):", "", choose_tags, None, on_cancel)
            else:
                choose_tags()

        def choose_tags(title=None):
            if title is not None:
                note.title = enc(title)
            if note.tagNames is None:
                self.window.show_input_panel("Tags (Optional):", default_tags, choose_notebook, None, on_cancel)
            else:
                choose_notebook()

        def choose_notebook(tags=None):
            if tags is not None:
                note.tagNames = extractTags(tags)
            if note.notebookGuid is None:
                self.window.show_quick_panel([notebook.name for notebook in notebooks], on_notebook)
            else:
                __send_note(note.notebookGuid)

        def on_notebook(notebook):
            if notebook >= 0:
                __send_note(notebooks[notebook].guid)
            else:
                on_cancel()

        def __send_note(notebookGuid):
            note.notebookGuid = notebookGuid

            LOG(note.title)
            LOG(note.tagNames)
            LOG(note.notebookGuid)

            try:
                sublime.status_message("Posting note, please wait...")
                if PY2:
                    cnote = noteStore.createNote(note)
                else:
                    cnote = noteStore.createNote(self.token(), note)
                sublime.status_message("Successfully posted note: guid:%s" % cnote.guid)
                self.view.settings().set("$evernote", True)
                self.view.settings().set("$evernote_guid", cnote.guid)
                self.view.settings().set("$evernote_title", cnote.title)
            except Errors.EDAMUserException as e:
                args = dict(title=note.title, notebookGuid=note.notebookGuid, tags=note.tagNames)
                if e.errorCode == 9:
                    self.connect(self.do_send, **args)
                else:
                    if sublime.ok_cancel_dialog('Error %s! retry?' % e):
                        self.connect(self.do_send, **args)
            except Exception as e:
                sublime.error_message('Error %s' % e)

        choose_title()


class SaveEvernoteNoteCommand(EvernoteDoText):

    def do_run(self, edit):
        note = Types.Note()
        noteStore = self.get_note_store()

        title = self.view.settings().get("$evernote_title")
        guid = self.view.settings().get("$evernote_guid")

        note.title = enc(title)
        note.guid = enc(guid)

        populate_note(note, self.view, self.get_notebooks())

        def __update_note():
            try:
                sublime.status_message("Updating note, please wait...")
                if PY2:
                    cnote = noteStore.updateNote(note)
                else:
                    cnote = noteStore.updateNote(self.token(), note)
                self.view.settings().set("$evernote", True)
                self.view.settings().set("$evernote_guid", cnote.guid)
                self.view.settings().set("$evernote_title", cnote.title)
                sublime.status_message("Successfully updated note: guid:%s" % cnote.guid)
            except Errors.EDAMUserException as e:
                if e.errorCode == 9:
                    self.connect(self.__update_note)
                else:
                    if sublime.ok_cancel_dialog('Error %s! retry?' % e):
                        self.connect(self.__update_note)
            except Exception as e:
                sublime.error_message('Error %s' % e)

        __update_note()

    def is_enabled(self):
        if self.view.settings().get("$evernote_guid", False):
            return True
        return False


class OpenEvernoteNoteCommand(EvernoteDoWindow):

    def do_run(self):
        from html2text import html2text
        noteStore = self.get_note_store()
        notebooks = self.get_notebooks()

        def on_notebook(notebook):
            if notebook < 0:
                return
            nid = notebooks[notebook].guid
            notes = noteStore.findNotesMetadata(
                self.token(), NoteStore.NoteFilter(notebookGuid=nid),
                0,
                100,
                NoteStore.NotesMetadataResultSpec(includeTitle=True)).notes
            notes.reverse()

            def on_note(i):
                if i < 0:
                    return
                sublime.status_message("Retrieving note \"%s\"..." % notes[i].title)
                # TODO: api v2
                note = noteStore.getNote(self.token(), notes[i].guid, True, False, False, False)
                newview = self.window.new_file()
                newview.set_scratch(True)
                newview.set_name(note.title)
                try:
                    mdtxt = html2text(note.content)
                    LOG("Conversion ok")
                except:
                    mdtxt = note.content
                    LOG("Conversion failed")
                    LOG(mdtxt)
                tags = [noteStore.getTag(self.token(), guid).name for guid in (note.tagGuids or [])]
                meta = "---\n"
                meta += "title: %s\n" % (note.title or "Untitled")
                meta += "tags: %s\n" % (json.dumps(tags))
                meta += "notebook: %s\n" % notebooks[notebook].name
                meta += "---\n\n"
                newview.settings().set("$evernote", True)
                newview.settings().set("$evernote_guid", note.guid)
                newview.settings().set("$evernote_title", note.title)
                append_to_view(newview, meta+mdtxt)
                syntax = newview.settings().get("md_syntax", "Packages/Markdown/Markdown.tmLanguage")
                newview.set_syntax_file(syntax)
                newview.show(0)
                sublime.status_message("Note \"%s\" opened!" % notes[i].title)

            sublime.set_timeout(lambda: self.window.show_quick_panel([note.title for note in notes], on_note), 0)
        self.window.show_quick_panel([notebook.name for notebook in notebooks], on_notebook)


class ReconfigEvernoteCommand(EvernoteDoWindow):

    def run(self):
        self.window = sublime.active_window()
        self.settings = sublime.load_settings(EVERNOTE_SETTINGS)
        self.settings.erase("token")
        EvernoteDo._noteStore = None
        EvernoteDo._notebooks = None
        self.connect(lambda: True)
