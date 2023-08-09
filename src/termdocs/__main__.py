#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import sys
from pathlib import Path
import logging
import textual
import textual.app
import textual.css.query
import textual.containers
import textual.reactive
import textual.widgets
import textual.color
from rich.console import RenderableType
from logging_handler import InternLoggingHandler
from textual.logging import TextualHandler as TextualLoggingHandler
from handlers.register import HANDLERS


logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.FileHandler("run.log", mode="w"), TextualLoggingHandler(), InternLoggingHandler()]
)


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").absolute()


class HelpPopup(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Static("TermDocs Help")
        with textual.containers.Container():
            yield textual.widgets.Static("Hello World")


class LoggingConsole(textual.widgets.RichLog):
    pass


class TermDocs(textual.app.App):
    CSS_PATH = "style.css"

    TITLE = "TermDocs"
    SUB_TITLE = str(ROOT)

    BINDINGS = [
        textual.app.Binding("ctrl+q", "quit", "Quit"),  # general unix-like (ctrl+c is also possible)
        textual.app.Binding("ctrl+x", "quit", "Quit", show=False),  # nano-like
        textual.app.Binding("f", "toggle_files", "Toggle Files"),
        textual.app.Binding("h", "toggle_help", "Toggle Help"),
        textual.app.Binding("ctrl+d", "toggle_dark", "Toggle Dark-Mode", show=False),
        textual.app.Binding("f1", "toggle_console", "Debug", show=False, priority=False)
    ]

    LOGGING_STACK = []

    path = textual.reactive.var(None)
    show_tree = textual.reactive.var(True)

    def watch_show_tree(self, show_tree: bool):
        self.set_class(show_tree, "-show-tree")

    def add_log(self, message: RenderableType):
        try:
            log = self.query_one(LoggingConsole)
        except textual.css.query.NoMatches:
            self.LOGGING_STACK.append(message)
        else:
            while self.LOGGING_STACK:
                log.write(self.LOGGING_STACK.pop(0), scroll_end=True)
            log.write(message, scroll_end=True)

    def compose(self) -> textual.app.ComposeResult:
        logging.debug("compose")
        yield textual.widgets.Header(show_clock=True)
        yield LoggingConsole(classes="-hidden", wrap=False, highlight=True, markup=True)
        with textual.containers.Container():
            yield HelpPopup(classes="-hidden")
            yield textual.widgets.DirectoryTree(ROOT, id="tree-view")
            yield textual.containers.VerticalScroll(id="file-view")
        yield textual.widgets.Footer()

    async def on_mount(self):
        logging.info("TermDocs is running")
        self.query_one(textual.widgets.DirectoryTree).focus()

    async def on_directory_tree_file_selected(self, event: textual.widgets.DirectoryTree.FileSelected):
        event.stop()
        self.path = event.path.absolute()
        logging.debug(f"Selected File: {self.path}")
        self.sub_title = self.validate_sub_title(self.path)
        container = self.query_one('#file-view', textual.containers.VerticalScroll)
        await container.remove_children()
        widget = textual.widgets.Static(f"TermDocs doesn't this support file ({self.path})")
        worth = 0
        for Handler in HANDLERS:
            compatibility = Handler.supports(self.path)
            if compatibility > worth:
                worth = compatibility
                widget = Handler(self.path)
        await container.mount(widget)

    async def action_toggle_help(self):
        logging.debug("Toggle Help")
        help_popup = self.query_one(HelpPopup)
        self.set_focus(None)
        if help_popup.has_class("-hidden"):
            help_popup.remove_class("-hidden")
        else:
            if help_popup.query("*:focus"):
                self.screen.set_focus(None)
            help_popup.add_class("-hidden")

    async def action_toggle_console(self):
        self.query_one(LoggingConsole).toggle_class("-hidden")

    async def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


if __name__ == '__main__':
    TermDocs().run()