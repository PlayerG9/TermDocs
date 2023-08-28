#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import pathlib
import textual
import textual.app
import textual.css.query
import textual.containers
import textual.reactive
import textual.widgets
import textual.color
import rich.text
from logging_handler import InternLoggingHandler, SpecialModuleLoggingFilter
from textual.logging import TextualHandler as TextualLoggingHandler
from handlers.register import HANDLERS
import configuration
from util import Compatibility
import widgets


logging.basicConfig(
    level=logging.DEBUG,
    format="{asctime} | {levelname:.3} | {name:10} | {module:15} | {funcName:20} | {lineno:3} | {message}",
    style='{',
    handlers=[
        logging.FileHandler("run.log", mode="w"),
        TextualLoggingHandler(),
        InternLoggingHandler()
    ],
)
for handler in logging.getLogger().handlers:
    handler.addFilter(SpecialModuleLoggingFilter())


CSS_PATHS = ["style.css", *configuration.args.css]


class LoggingConsole(textual.widgets.RichLog):
    pass


class TermDocs(textual.app.App):
    CSS_PATH = CSS_PATHS

    TITLE = "TermDocs"
    SUB_TITLE = str(configuration.index_file)

    BINDINGS = [
        textual.app.Binding("ctrl+q", "quit", "Quit"),  # general unix-like (ctrl+c is also possible)
        textual.app.Binding("ctrl+x", "quit", "Quit", show=False),  # nano-like
        textual.app.Binding("f", "toggle_files", "Toggle Files"),
        # textual.app.Binding("h", "toggle_help", "Toggle Help"),
        textual.app.Binding("ctrl+d", "toggle_dark", "Toggle Dark-Mode", show=False),
        textual.app.Binding("f1", "toggle_help", "Toggle Help", show=True, priority=True),
        textual.app.Binding("f4", "toggle_console", "Debug", show=False, priority=True),
        textual.app.Binding("f5", "screenshot", "Screenshot", show=False, priority=True),
    ]

    LOGGING_STACK = []

    path = textual.reactive.var(configuration.index_file)
    show_tree = textual.reactive.var(True)

    def watch_show_tree(self, show_tree: bool):
        self.set_class(show_tree, "-show-tree")

    async def watch_path(self):
        logging.debug(f"Selected File: {self.path}")
        self.sub_title = self.validate_sub_title(self.path)  # noqa
        container = self.query_one('#file-view', textual.containers.VerticalScroll)
        await container.remove_children()
        if not self.path:
            pass  # nothing
        elif not self.path.is_file():
            widget = textual.widgets.Static(
                f"The file {self.format_path(self.path)} doesn't exist"
            )
            await container.mount(widget)
        else:
            widget = textual.widgets.Static(
                rich.text.Text(f"TermDocs doesn't this support file ({self.format_path(self.path)})")
                + rich.text.Text('\n') +
                rich.text.Text("open as text", style=rich.text.Style.from_meta({'@click': "open_as_text()"}))
            )
            compatibility = Compatibility.NONE
            for Handler in HANDLERS:
                handler_comp = Handler.supports(self.path)
                if handler_comp and handler_comp > compatibility:
                    compatibility = handler_comp
                    widget = Handler(self.path)
            await container.mount(widget)

    def add_log(self, message: textual.app.RenderableType):
        try:
            log = self.query_one(LoggingConsole)
        except textual.css.query.NoMatches:
            self.LOGGING_STACK.append(message)
        else:
            while self.LOGGING_STACK:
                log.write(self.LOGGING_STACK.pop(0), scroll_end=True)
            log.write(message, scroll_end=True)

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Header(show_clock=True)
        yield LoggingConsole(classes="-hidden", wrap=False, highlight=True, markup=True)
        with textual.containers.Container():
            yield widgets.HelpWidget(classes="-hidden")
            yield textual.widgets.DirectoryTree(configuration.root_dir, id="tree-view")
            yield textual.containers.VerticalScroll(id="file-view")
        yield textual.widgets.Footer()

    async def on_mount(self):
        logging.info("TermDocs is running")
        self.query_one(textual.widgets.DirectoryTree).focus()
        self.show_tree = not configuration.is_custom_file

    async def on_directory_tree_file_selected(self, event: textual.widgets.DirectoryTree.FileSelected):
        event.stop()
        self.path = event.path.absolute()

    async def action_toggle_help(self):
        help_popup = self.query_one(widgets.HelpWidget)
        self.set_focus(None)
        if help_popup.has_class("-hidden"):
            help_popup.remove_class("-hidden")
            await help_popup.ensure_rendered()
        else:
            if help_popup.query("*:focus"):
                self.screen.set_focus(None)
            help_popup.add_class("-hidden")

    async def action_toggle_console(self):
        self.query_one(LoggingConsole).toggle_class("-hidden")

    async def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree

    async def action_open_as_text(self):
        from handlers.text_handler import TextHandler
        container = self.query_one('#file-view', textual.containers.VerticalScroll)
        await container.remove_children()
        await container.mount(TextHandler(path=self.path))

    @staticmethod
    def format_path(path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(configuration.root_dir))
        except ValueError:
            return str(path)


if __name__ == '__main__':
    TermDocs().run()
