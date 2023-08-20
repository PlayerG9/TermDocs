#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import functools
from pathlib import Path
import textual.events
import textual.widget
import textual.widgets
import textual.reactive
import textual.containers
from textual.app import ComposeResult
import rich.syntax
from rich.text import Text
from rich.style import Style
import markdown_it
import markdown_it.tree
import markdown_it.token
import markdownify
from .color_image import ColorImage
from .detail_image import DetailImage


BULLETS = ["\u25CF ", "▪ ", "‣ ", "• ", "⭑ "]
NUMERALS = " ⅠⅡⅢⅣⅤⅥ"


class MarkdownElement(textual.widget.Widget):
    DEFAULT_CSS = r"""
    MarkdownElement {
        height: auto;
    }
    """

    def __init__(self, node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
        self.node = node
        self.root = root
        super().__init__()

    async def action_link(self, href: str) -> None:
        """Called on link click."""
        logging.debug(f"action_link({href!r})")
        if href.startswith("#"):
            widget = self.app.query_one(href)
            self.scroll_to_center(widget=widget, animate=True)
        else:
            self.post_message(CustomMarkdown.LinkClicked(root=self.root, href=href))


class MarkdownStatic(MarkdownElement):
    _renderable: textual.app.RenderableType

    def __init__(
        self,
        renderable: textual.app.RenderableType,
        root: 'CustomMarkdown',
    ) -> None:
        textual.widget.Widget.__init__(self)
        self.root = root
        self.renderable = renderable

    def render(self) -> textual.app.RenderableType:
        return self.renderable


class MarkdownInline(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownInline {
        layout: vertical;
    }
    .em {
        text-style: italic;
    }
    .strong {
        text-style: bold;
    }
    .s {
        text-style: strike;
    }
    .code_inline {
        text-style: bold dim;
        background: $background-lighten-2;
    }
    """

    COMPONENT_CLASSES = {"em", "strong", "s", "code_inline"}

    def _recursive_compose(self, node, style=None):
        style = style or Style()

        for node in node.children:
            if node.type == "text":
                yield Text(text=node.content, style=style)
            elif node.type == "hardbreak":
                yield Text(text='\n')
            elif node.type == "softbreak":
                yield Text(text=' ', style=style)
            elif node.type == "image":
                yield MarkdownImage(node=node, root=self.root)
            elif node.type == "link":
                href = node.attrGet('href')
                action = f"link({href!r})"
                yield from self._recursive_compose(
                    node=node,
                    style=style + Style.from_meta({"@click": action})
                )
            elif node.type == "code_inline":
                yield Text(
                    text=node.content,
                    style=style + self.get_component_rich_style(node.type, partial=True)
                )
            # italic | bold | strikethrough
            elif node.type in {'em', 'strong', 's'}:
                yield from self._recursive_compose(
                    node=node,
                    style=style + self.get_component_rich_style(node.type, partial=True)
                )
            else:
                logging.debug(f"Unknown node-type: {node.type}")

    def _clean_compose(self, composed: iter):
        text = Text()
        for item in composed:
            if isinstance(item, Text):
                text.append_text(item)
            else:
                yield MarkdownStatic(text, root=self.root)
                text = Text()
                yield item
        yield MarkdownStatic(text, root=self.root)

    def compose(self) -> ComposeResult:
        yield from self._clean_compose(
            self._recursive_compose(self.node)
        )


class MarkdownHorizontalRule(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownHorizontalRule {
        border-bottom: heavy $primary;
        height: 1;
        padding-top: 1;
        margin-bottom: 1;
    }
    """


class MarkdownHeading(MarkdownElement):
    DEFAULT_CSS = r"""
    .h1 {
        background: $accent-darken-2;
        border: wide $background;
        content-align: center middle;

        padding: 1;
        text-style: bold;
        color: $text;
    }
    .h2 {
        background: $panel;
        border: wide $background;
        text-align: center;
        text-style: underline;
        color: $text;
        padding: 1;
        text-style: bold;
    }
    .h3 {
        background: $surface;
        text-style: bold;
        color: $text;
        border-bottom: wide $foreground;
        width: auto;
    }
    .h4 {
        text-style: underline;
        margin: 1 0;
    }
    .h5 {
        text-style: bold;
        color: $text;
        margin: 1 0;
    }
    .h6 {
        text-style: bold;
        color: $text-muted;
        margin: 1 0;
    }
    .em {
        text-style: italic;
    }
    .strong {
        text-style: bold;
    }
    .s {
        text-style: strike;
    }
    .code_inline {
        text-style: bold dim;
        background: $background-lighten-2;
    }
    """

    COMPONENT_CLASSES = {"em", "strong", "s", "code_inline"}

    def _render_inline(self, node: markdown_it.tree.SyntaxTreeNode, style: Style = None) -> Text:
        text = Text()
        style = style or Style()

        for node in node.children:
            if node.type == "text":
                text.append(text=node.content, style=style)
            elif node.type == "hardbreak":
                text.append(text='\n')
            elif node.type == "softbreak":
                text.append(text=' ', style=style)
            elif node.type == "image":
                _style = style
                txt = "🖼"
                href = node.attrGet("src")
                if href:
                    action = f"link({href!r})"
                    _style = style + Style.from_meta({'@click': action})
                alt = node.attrGet("alt")
                if alt:
                    txt += f" ({alt})"
                text.append(
                    text=txt,
                    style=_style
                )
            elif node.type == "link":
                href = node.attrGet('href')
                action = f"link({href!r})"
                text.append(
                    self._render_inline(
                        node=node,
                        style=style + Style.from_meta({"@click": action})
                    )
                )
            elif node.type == "code_inline":
                text.append(
                    text=node.content,
                    style=style + self.get_component_rich_style(node.type, partial=True)
                )
            # italic | bold | strikethrough
            elif node.type in {'em', 'strong', 's'}:
                text.append(
                    self._render_inline(
                        node=node,
                        style=style + self.get_component_rich_style(node.type, partial=True)
                    )
                )
            else:
                logging.debug(f"Unknown node-type: {node.type}")
        return text

    def _render_plaintext(self, node: markdown_it.tree.SyntaxTreeNode) -> str:
        text = []
        for node in node.children:
            if node.type == "text":
                text.append(node.content)
            elif node.children:
                text.append(self._render_plaintext(node=node))
        return ''.join(text)

    def _generate_id(self):
        r"""
        Valid Identifier: '[a-zA-Z_\-][a-zA-Z0-9_\-]*'
        """
        import re
        plain = self._render_plaintext(node=self.node)
        plain = plain.strip().lower().replace(' ', '-')
        head_match = re.match(r"[^a-zA-Z_\-]*([a-zA-Z_\-])", plain)
        head = head_match.group(1)
        body_matches = re.finditer(r"[a-zA-Z0-9_\-]+", plain[head_match.end():])
        return head + ''.join(_.group() for _ in body_matches)

    def on_mount(self):
        self.id = self._generate_id()
        logging.debug(f"Header with id='{self.id}'")
        self.add_class(self.node.tag)

    @functools.cache
    def render(self) -> textual.app.RenderableType:
        return self._render_inline(self.node.children[0])


class MarkdownParagraph(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownParagraph {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownImage(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownImage {
        width: 1fr;
        height: 70vh;
    }
    """

    detailed: bool = textual.reactive.reactive(False)

    @functools.cached_property
    def href(self) -> str:
        import os.path as p
        href = self.node.attrGet("src")
        if ColorImage.check_is_file(href) and not p.isabs(href):
            href = p.join(self.root.DIR, href)
        return href

    async def watch_detailed(self):
        await self.update()

    def compose(self) -> textual.app.ComposeResult:
        yield textual.containers.Container()

    async def _set_image_widget(self, widget: textual.widget.Widget):
        container = self.query_one(textual.containers.Container)
        with self.app.batch_update():
            await container.remove_children()
            await container.mount(widget)

    async def on_mount(self):
        await self.update()

    async def update(self):
        await self._set_image_widget(
            (DetailImage if self.detailed else ColorImage)(src=self.href)
        )

    async def on_click(self, event: textual.events.Click):
        if event.button in {2, 3}:  # middle- or right-click
            event.stop()
            self.detailed = not self.detailed


class MarkdownBlockQuote(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownBlockQuote {
        layout: vertical;
        border-left: outer $primary;
        background: $background-lighten-1;
        padding: 1 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownListItem(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownListItem {
        layout: vertical;
        padding-left: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownListItemIcon(MarkdownStatic):
    pass


class _MarkdownList(MarkdownElement):
    DEFAULT_CSS = r"""
    _MarkdownList {
        layout: vertical;
    }
    """

    @functools.cached_property
    def list_depth(self) -> int:
        depth = 0
        p = self.node.parent
        while p:
            if p.type in {'bullet_list', 'ordered_list'}:
                depth += 1
            p = p.parent
        return depth

    @functools.cached_property
    def depth(self) -> int:
        depth = 0
        p = self.node.parent
        while p:
            if p.type == self.node.type:
                depth += 1
            p = p.parent
        return depth

    def get_icon(self, i: int) -> str:
        raise NotImplementedError()

    def compose(self) -> ComposeResult:
        for i, element in enumerate(render_node(node=self.node, root=self.root)):
            yield MarkdownListItemIcon(self.get_icon(i), root=self.root)
            yield element


class MarkdownOrderedList(_MarkdownList):
    def get_icon(self, i: int) -> str:
        return f"{i + 1}."


class MarkdownBulletList(_MarkdownList):
    def get_icon(self, i: int) -> str:
        return BULLETS[self.depth % len(BULLETS)]


class MarkdownCodeBlock(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownCodeBlock {
        background: $background-lighten-2;
    }
    """

    SIZE2LANGUAGES = {'html', 'css', 'scss', 'sass', 'sql', 'yaml', 'json', 'xml'}

    def __init__(self, node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
        super().__init__(node=node, root=root)
        self._code = node.content
        self._language = node.info
        self._renderable = rich.syntax.Syntax(
            code=self._code,
            lexer=self._language,
            theme='ansi_dark',
            dedent=True,
            line_numbers=self.node.type == "fence",
            # code_width=80,
            tab_size=2 if self._language in self.SIZE2LANGUAGES else 4,
            word_wrap=False,
            background_color=None,
            indent_guides=False,
            padding=0,
        )

    def render(self) -> textual.app.RenderableType:
        return self._renderable


class MarkdownHtmlBlock(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownHtmlBlock {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        markdown = markdownify.markdownify(html=self.node.content)
        parser = markdown_it.MarkdownIt(
            config="commonmark",
            # config="gfm-like",  # github-flavored-markdown
        )
        tokens = parser.parse(src=markdown)
        node = markdown_it.tree.SyntaxTreeNode(tokens=tokens)
        yield from render_node(node=node, root=self.root)


class UnknownElement(MarkdownElement):
    def render(self) -> textual.app.RenderableType:
        return Text(f"{self.node}", style=Style.parse("on red"))


HTML_MAP = dict(
    inline=MarkdownInline,
    hr=MarkdownHorizontalRule,
    heading=MarkdownHeading,
    paragraph=MarkdownParagraph,
    image=MarkdownImage,
    code_block=MarkdownCodeBlock,
    fence=MarkdownCodeBlock,
    ordered_list=MarkdownOrderedList,
    bullet_list=MarkdownBulletList,
    list_item=MarkdownListItem,
    blockquote=MarkdownBlockQuote,
    html_block=MarkdownHtmlBlock,
)


def render_node(node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
    for node in node.children:
        logging.debug(f"{node}")
        yield HTML_MAP.get(node.type, UnknownElement)(node=node, root=root)


class CustomMarkdown(textual.widget.Widget):
    DEFAULT_CSS = r"""
    CustomMarkdown {
        layout: vertical;
        height: auto;
        margin: 1 4 1 4;
    }
    """

    DIR = Path.cwd()

    def __init__(self, file: Path = None):
        super().__init__()
        self.file = file

    class LinkClicked(textual.widget.Message, bubble=True):
        def __init__(self, root: 'CustomMarkdown', href: str):
            super().__init__()
            self.href = href
            self.root = root

        @property
        def control(self) -> 'CustomMarkdown':
            return self.root

    async def on_mount(self):
        if self.file:
            await self.load(self.file)

    async def load(self, file: Path):
        self.DIR = file.parent
        await self.update(file.read_text(encoding='utf-8'))

    async def update(self, markdown: str):
        parser = markdown_it.MarkdownIt(
            config="commonmark",
            # config="gfm-like",  # github-flavored-markdown
        )

        tokens = parser.parse(markdown)
        root_node = markdown_it.tree.SyntaxTreeNode(tokens, create_root=True)

        widgets = render_node(node=root_node, root=self)

        with self.app.batch_update():
            await self.remove_children()
            await self.mount_all(widgets)
