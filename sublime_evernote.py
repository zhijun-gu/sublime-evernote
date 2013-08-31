#coding:utf-8
import sys
sys.path.append("lib")
sys.path.append("lib/evernote-sdk-python/lib")
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
from evernote.api.client import EvernoteClient
from html import XHTML
import sublime
import sublime_plugin
import webbrowser
import markdown2


settings = sublime.load_settings("SublimeEvernote.sublime-settings")


class SendToEvernoteCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view
        self.window = sublime.active_window()

    def to_markdown_html(self):
        region = sublime.Region(0, self.view.size())
        encoding = self.view.encoding()
        if encoding == 'Undefined':
            encoding = 'utf-8'
        elif encoding == 'Western (Windows 1252)':
            encoding = 'windows-1252'
        contents = self.view.substr(region)

        markdown_html = markdown2.markdown(contents, extras=['footnotes', 'fenced-code-blocks', 'cuddled-lists', 'code-friendly', 'metadata'])
        
        return markdown_html


    def connect(self, callback, **kwargs):
        sublime.status_message("initializing..., please wait...")

        def __connect(token):
            settings.set("token", token)
            sublime.save_settings("SublimeEvernote.sublime-settings")
            callback(**kwargs)

        def on_token(token):
            if token:
                __connect(token)

        token = settings.get("token")
        if not token:
            webbrowser.open_new_tab(
                "https://www.evernote.com/api/DeveloperToken.action")
            self.window.show_input_panel(
                "token (required)::", "", on_token, None, None)
        else:
            __connect(token)

    def send_note(self, **kwargs):
        token = settings.get("token")
        noteStore = EvernoteClient(token=token, sandbox=False).get_note_store()
        region = sublime.Region(0L, self.view.size())
        content = self.view.substr(region)

        markdown_html = self.to_markdown_html()

        def __send_note(title, tags):
            xh = XHTML()
            note = Types.Note()
            note.title = title.encode('utf-8')
            note.content = '<?xml version="1.0" encoding="UTF-8"?>'
            note.content += '<!DOCTYPE en-note SYSTEM \
                "http://xml.evernote.com/pub/enml2.dtd">'
            note.content += '<en-note>%s'%markdown_html.encode('utf-8')
            note.content += '</en-note>'
            note.tagNames = tags and tags.split(",") or []
            try:
                sublime.status_message("please wait...")
                cnote = noteStore.createNote(note)
                sublime.status_message("send success guid:%s" % cnote.guid)
                sublime.message_dialog("success")
            except Errors.EDAMUserException, e:
                args = dict(title=title, tags=tags)
                if e.errorCode == 9:
                    self.connect(self. send_note, **args)
                else:
                    if sublime.ok_cancel_dialog('error %s! retry?' % e):
                        self.connect(self.send_note, **args)
            except Exception, e:
                sublime.error_message('error %s' % e)

        def on_title(title):
            def on_tags(tags):
                __send_note(title, tags)
            self.window.show_input_panel(
                "Tags (Optional)::", "", on_tags, None, None)

        if not kwargs.get("title"):
            self.window.show_input_panel(
                "Title (required)::", "", on_title, None, None)
        else:
            __send_note(kwargs.get("title"), kwargs.get("tags"))

    def run(self, edit):
        if not settings.get("token"):
            self.connect(self.send_note)
        else:
            self.send_note()
