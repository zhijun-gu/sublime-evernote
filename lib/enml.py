import mistune
import yaml

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class ENMLConversionError(Exception):
    pass


class ENMLRenderer(mistune.Renderer):

    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)

renderer = ENMLRenderer()
md = mistune.Markdown(renderer=renderer)


def enml_from_md(text):
    metadata = {}
    # Metadata detection is very strict (for performance)
    if text.startswith("---\n"):
        end_meta = text.find("\n---\n", 4)
        if end_meta > 0:
            metadata = yaml.load(text[4:end_meta])
            text = text[end_meta + 5:]
    return (metadata, md(text))


def metadata_from_obj(obj):
    return "---\n%s\n---\n" % yaml.dump(obj)


def has_metadata(text):
    return text.startswith("---\n") and text.find("\n---\n", 4) > 0
