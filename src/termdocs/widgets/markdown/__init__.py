#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""
TODO: html_inline in text/header
"""
import logging
import random
import functools
import typing as t
from pathlib import Path
import textual.events
import textual.widget
import textual.widgets
import textual.reactive
import textual.containers
from textual.app import ComposeResult
import rich.syntax
from rich.text import Text, Style
import markdown_it
import markdown_it.tree
import markdown_it.token
import markdownify
from util import HyperRef
from util.constants import SIZE2LANGUAGES
from ..color_image import ColorImage
from ..detail_image import DetailImage
from . import plugins as markdown_plugins
from ._emojis import EMOJIS as EMOJI_MAPPING


BULLETS = ["\u25CF ", "▪ ", "‣ ", "• ", "⭑ "]
NUMERALS = " ⅠⅡⅢⅣⅤⅥ"

markdown_parser = markdown_it.MarkdownIt(
    # config="commonmark",
    config="gfm-like",  # github-flavored-markdown
)
markdown_parser.use(markdown_plugins.front_matter_plugin)
markdown_parser.use(markdown_plugins.emoji_plugin)
markdown_parser.use(markdown_plugins.toc_plugin)
markdown_parser.use(markdown_plugins.attrs_plugin)
markdown_parser.use(markdown_plugins.attrs_block_plugin)
markdown_parser.use(markdown_plugins.footnote_plugin)


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
        attr_id = node.attrGet("id")
        if attr_id:
            self.id = attr_id
        classes = node.attrGet('class')
        if classes:
            self.add_class(*classes.split())

    async def action_link(self, href: str) -> None:
        """Called on link click."""
        logging.debug(f"action_link({href!r})")
        if HyperRef.check_is_idref(href):
            self.scroll_to_header(href=href)
        else:
            self.post_message(CustomMarkdown.LinkClicked(root=self.root, href=href))

    def scroll_to_header(self, href: str):
        for id_, should_warn in self.iterate_possible_ids(href):
            try:
                widget = self.root.query_one(id_)
            except textual.app.NoMatches:
                continue
            else:
                if should_warn:
                    self.notify(
                        message=f"Header {href!r} not found and {id_!r} was used instead",
                        severity='warning',
                        timeout=5
                    )
                logging.debug(f"Scrolling to widget {href}")
                self.scroll_to_center(widget=widget, animate=True)
                break
        else:
            logging.error(f"Header {href!r} not found in the document")
            self.notify(
                message=f"Header {href!r} or similar not found in this document",
                title="Header not found",
                severity='error',
                timeout=5,
            )

    def iterate_possible_ids(self, id_: str):
        yield id_, False
        high_similar = self.get_closest_id(id_, cutoff=0.8)
        if high_similar:
            yield high_similar, False
        low_similar = self.get_closest_id(id_, cutoff=0.4)
        if low_similar:
            yield low_similar, True

    @property
    def all_ids(self) -> t.List[str]:
        return [
            f"#{widget.id}" for widget in self.root.query(None) if widget.id
        ]

    def get_closest_id(self, id_: str, cutoff=0.6) -> t.Optional[str]:
        import difflib
        matches = difflib.get_close_matches(id_, self.all_ids, n=1, cutoff=cutoff)
        return matches[0] if matches else None


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
    .footnote {
        text-style: italic dim;
    }
    """

    COMPONENT_CLASSES = {"em", "strong", "s", "code_inline", "footnote"}

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
            elif node.type == "emoji":
                emoji = EMOJI_MAPPING.get(node.content) or f":{node.content}:"
                yield Text(text=emoji, style=style)
            elif node.type == "footnote_ref":
                footnote_id = node.meta['id']
                action = f"link({f'#footnote-{self.root.DOCUMENT_ID}-{footnote_id}'!r})"
                yield Text(
                    text=f"^{footnote_id}",
                    style=style + self.get_component_rich_style("footnote") + Style.from_meta({"@click": action})
                )
            else:
                logging.warning(f"Unknown inline node-type: {node.type}")
                logging.debug(f"{vars(node)}")

    def _clean_compose(self, composed: iter):
        text = Text()
        next_sibling = self.node.next_sibling
        if next_sibling and next_sibling.type == "footnote_anchor":
            text.append(text=f"^{next_sibling.meta['id']}: ", style=Style(dim=True, italic=True))

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
        padding-top: 1
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
    .footnote {
        text-style: italic dim;
    }
    """

    COMPONENT_CLASSES = {"em", "strong", "s", "code_inline", "footnote"}

    def __init__(self, node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
        super().__init__(node=node, root=root)
        if self.id is None:
            self.id = self._generate_id()
        logging.info(f"Header with id='{self.id}'")
        self.add_class(self.node.tag)

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
                        style=style + self.get_component_rich_style("footnote") + Style.from_meta({"@click": action})
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
            elif node.type == "emoji":
                emoji = EMOJI_MAPPING.get(node.content) or f":{node.content}:"
                text.append(text=emoji, style=style)
            elif node.type == "footnote_ref":
                footnote_id = node.meta['id']
                action = f"link({f'#footnote-{self.root.DOCUMENT_ID}-{footnote_id}'!r})"
                text.append(
                    text=f"[^{footnote_id}]",
                    style=style + Style.from_meta({"@click": action})
                )
            else:
                logging.warning(f"Unknown inline node-type: {node.type}")
                logging.debug(f"{vars(node)}")
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
        plain = self.rendered_plaintext
        plain = plain.strip().lower().replace(' ', '-')
        head_match = re.match(r"[a-zA-Z_\-]", plain)
        head = head_match.group()
        body_matches = re.finditer(r"[a-zA-Z0-9_\-]+", plain[head_match.end():])
        base_id = head + ''.join(_.group() for _ in body_matches)
        real_id = base_id
        i = 0
        while True:
            try:
                self.app.query_one(f"#{real_id}")
            except textual.app.NoMatches:
                break
            else:
                i += 1
                real_id = f"{base_id}-{i}"
        return real_id

    @functools.cached_property
    def rendered_text(self) -> Text:
        return self._render_inline(self.node.children[0])

    @functools.cached_property
    def rendered_plaintext(self) -> str:
        return self._render_plaintext(node=self.node)

    def render(self) -> textual.app.RenderableType:
        return self.rendered_text


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
        max-height: 50w;
    }
    """

    _detailed: bool = None

    @functools.cached_property
    def href(self) -> str:
        href = HyperRef(self.node.attrGet("src"))
        if href.check_is_file():
            return str(href.absolute(to=self.root.DIR))
        else:
            return str(href)

    def compose(self) -> textual.app.ComposeResult:
        yield textual.containers.Container()

    async def _set_image_widget(self, widget: textual.widget.Widget):
        container = self.query_one(textual.containers.Container)
        with self.app.batch_update():
            await container.remove_children()
            await container.mount(widget)

    async def on_mount(self):
        # this ensures that the markdown-content is loaded and rendered before the images are
        # because images are "expensive" to load and render
        self.set_timer(0.1, self.update_color_widget)
        # await self.update_color_widget()

    async def update_color_widget(self, detailed: bool = False):
        if detailed == self._detailed:
            return
        self._detailed = detailed
        await self._set_image_widget(
            (DetailImage if detailed else ColorImage)(src=self.href)
        )

    async def on_click(self, event: textual.events.Click):
        if event.button in {2, 3}:  # middle- or right-click
            event.stop()
            await self.update_color_widget(not self._detailed)


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

    def __init__(self, node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
        super().__init__(node=node, root=root)
        self._code = node.content.strip()
        self._language = node.info
        self._renderable = rich.syntax.Syntax(
            code=self._code,
            lexer=self._language,
            theme='ansi_dark',
            dedent=True,
            line_numbers=bool(self._language),
            # code_width=80,
            tab_size=2 if self._language in SIZE2LANGUAGES else 4,
            word_wrap=False,
            background_color=None,
            indent_guides=False,
            padding=0,
        )

    def render(self) -> textual.app.RenderableType:
        return self._renderable


class MarkdownTable(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTable {
        layout: vertical;
        border: round $primary-background-lighten-2;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownTableSeparator(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTableSeparator {
        height: 1;
        border-top: solid $primary-background-lighten-2;
    }
    """

    def __init__(self):
        textual.widget.Widget.__init__(self)


class MarkdownTableHead(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTableHead {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownTableBody(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTableBody {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        for element in render_node(node=self.node, root=self.root):
            yield MarkdownTableSeparator()
            yield element


class MarkdownTr(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTr {
        layout: horizontal;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownTh(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTh {
        layout: vertical;
        text-style: bold italic;
        width: 1fr;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownTd(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownTd {
        layout: vertical;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownHtmlBlock(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownHtmlBlock {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        markdown = markdownify.markdownify(html=self.node.content)
        tokens = markdown_parser.parse(src=markdown)
        node = markdown_it.tree.SyntaxTreeNode(tokens=tokens)
        yield from render_node(node=node, root=self.root)


class MarkdownFrontMatter(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownFrontMatter {
        color: $text-muted;
    }
    """

    def render(self) -> textual.app.RenderableType:
        return self.node.content


class MarkdownToc(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownToc {
        padding: 1;
    }
    """

    @functools.cached_property
    def headings(self) -> t.Iterable[t.Tuple[int, MarkdownHeading]]:
        max_depth = self.node.attrGet("depth")
        max_depth = int(max_depth) if max_depth and max_depth.isdigit() else 3
        for widget in self.root.walk_children(MarkdownHeading, method='depth'):
            level = len(widget.node.markup)
            if level > max_depth or widget.has_class("no_toc"):
                continue
            yield level, widget

    @staticmethod
    def _bullet_list_icon(_) -> str:
        return "\u25CF"

    @staticmethod
    def _number_list_icon(i: int) -> str:
        return f"{i}."

    @functools.cached_property
    def _rendered(self) -> Text:
        dot_style = self.node.attrGet('style') in {'-', '*', 'list', 'ul'}
        get_icon = self._bullet_list_icon if dot_style else self._number_list_icon

        text = Text()
        text.append(
            text="📖 Table of Contents\n",
            style=Style(bold=True, italic=True)
        )
        stack = []
        for level, heading in self.headings:
            while level > len(stack):
                stack.append(0)
            while level < len(stack):
                stack.pop(-1)
            stack[-1] += 1

            text.append(text=f"{'  ' * level}{get_icon(stack[-1])} ")
            text.append(
                text=heading.rendered_plaintext,
                style=Style.from_meta({'@click': f"link({('#'+heading.id)!r})"})
            )
            text.append(text='\n')
        return text

    def render(self) -> textual.app.RenderableType:
        return self._rendered


class MarkdownFootnoteBlock(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownFootnoteBlock {
        layout: vertical;
        color: $text-muted;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


class MarkdownFootnote(MarkdownElement):
    DEFAULT_CSS = r"""
    MarkdownFootnote {
        layout: horizontal;
    }
    """

    def on_mount(self):
        logging.debug(f"Footnote: {vars(self.node)}")

    def compose(self) -> ComposeResult:
        yield from render_node(node=self.node, root=self.root)


# TODO: backref to place in document!?
class MarkdownFootnoteAnchor(MarkdownFootnote):
    DEFAULT_CSS = r"""
    MarkdownFootnoteAnchor {
        height: 0;
    }
    """

    def __init__(self, node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
        super().__init__(node=node, root=root)
        footnote_id = self.node.meta['id']
        self.id = f'footnote-{self.root.DOCUMENT_ID}-{footnote_id}'


class UnknownElement(MarkdownElement):
    def on_mount(self):
        logging.warning(f"Unknown node-type: {self.node.type}")
        logging.debug(f"{vars(self.node)}")

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
    # gfm-like
    table=MarkdownTable,
    thead=MarkdownTableHead,
    tbody=MarkdownTableBody,
    tr=MarkdownTr,
    th=MarkdownTh,
    td=MarkdownTd,
    # plugins
    front_matter=MarkdownFrontMatter,
    toc=MarkdownToc,
    footnote_block=MarkdownFootnoteBlock,
    footnote=MarkdownFootnote,
    footnote_anchor=MarkdownFootnoteAnchor,
)


def render_node(node: markdown_it.tree.SyntaxTreeNode, root: 'CustomMarkdown'):
    for node in node.children:
        node_type = HTML_MAP.get(node.type, UnknownElement)
        yield node_type(node=node, root=root)


class CustomMarkdown(textual.widget.Widget):
    DEFAULT_CSS = r"""
    CustomMarkdown {
        layout: vertical;
        height: auto;
        margin: 1 4 1 4;
    }
    """

    DIR = Path.cwd()
    TOKENS: t.List[markdown_it.token.Token] = None
    ROOT_NODE: markdown_it.tree.SyntaxTreeNode = None
    DOCUMENT_ID: str = random.randbytes(4).hex()

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
        await self.update(markdown=file.read_text(encoding='utf-8'), src_dir=file.parent)

    async def update(self, markdown: str, src_dir: t.Union[str, Path] = None):
        self.DOCUMENT_ID = random.randbytes(4).hex()
        logging.debug(f"Loading Markdown-Document with generated id {self.DOCUMENT_ID!r}")
        self.DIR = Path(src_dir) if src_dir else Path.cwd()

        self.TOKENS = tokens = markdown_parser.parse(markdown)
        self.ROOT_NODE = root_node = markdown_it.tree.SyntaxTreeNode(tokens, create_root=True)

        widgets = render_node(node=root_node, root=self)

        with self.app.batch_update():
            await self.remove_children()
            await self.mount_all(widgets)
