#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from __version__ import __version__
import logging
import webbrowser
import textual.app
import textual.widget
from .markdown import CustomMarkdown as Markdown
from util import HyperRef


MESSAGE = f"""
# TermDocs v{__version__}

{{: depth=2 }}
[[TOC]]

![logo](data:image/png;base64,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)

## About TermDocs

TermDocs is an interactive terminal markdown-documentation viewer with support for all markdown features.

## Shortcuts

| Shortcut              | Action           | Description                                 |
|-----------------------|------------------|---------------------------------------------|
| `ctrl+q`/`ctrl+x`     | Quit             | Closes TermDocs and returns to the terminal |
| `f`                   | Toggle Files     | Toggle the File-Tree                        |
| `ctrl+d`              | Toggle Dark Mode | Don't know why you would want that          |
| `f1`                  | Toggle Help      | Toggle this Help-Message                    |
| `f4`                  | Toggle Console   | Toggle the Debug-Console                    |
| `f5`                  | Screenshot       | Saves the current window as an svg-image    |

## More

- [GitHub Repository](https://github.com/PlayerG9/TermDocs)
- [Online Documentation](https://PlayerG9.github.com/TermDocs/)

## Markdown Specifications

TermDocs supports the commonmark specification with some additional features.\
The features are:\

### strikethrough

Text can be ~~be crossed out~~ by using `~~text~~`

### Tables

Tables are allowed

| Header-1 | Header-2 | Header-3   |
|----------|----------|------------|
| Row-1    | `code`   | **bold**   |
| Row-2    | *italic* | ~~strike~~ |

    | Header-1 | Header-2 | Header-3   |
    |----------|----------|------------|
    | Row-1    | `code`   | **bold**   |
    | Row-2    | *italic* | ~~strike~~ |

### Attributes

{{: .warning }}
> per default styles are only loaded when TermDocs is started with the `--md-css` option

{{: #custom-id .italic }}
> Block level attributes

Or inline `inline attributes`{{: .italic }}

    {{: #custom-id .italic }}
    > Block level attributes
    
    Or `inline attributes`{{: .italic }}

(doesn't quite work yet for inline)

### Automatic Table of Contents (TOC)

[[TOC]]

    [[TOC]]
    
    {{:toc}}


"""


class HelpWidget(textual.widget.Widget):
    DEFAULT_CSS = r"""
    HelpWidget .italic {
        text-style: italic;
    }
    HelpWidget .warning {
        background: $warning-darken-3;
    }
    """

    def compose(self) -> textual.app.ComposeResult:
        yield Markdown()

    async def on_mount(self):
        await self.query_one(Markdown).update(markdown=MESSAGE)

    @textual.on(Markdown.LinkClicked)
    async def on_link_clicked(self, event: Markdown.LinkClicked):
        href = HyperRef(event.href)
        logging.debug(f"Open url in browser: {href!r}")
        if not webbrowser.open(url=str(href)):
            logging.error(f"Can't open url: {href}")
            self.notify(
                message=f"{href}",
                title="Can't open url",
                severity='error',
                timeout=10,
            )
