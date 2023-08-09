#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from logging import Handler, LogRecord
from textual.logging import active_app


class InternLoggingHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        """Invoked by logging."""
        message = self.format(record)
        try:
            app = active_app.get()
        except LookupError as exc:
            print("Failed to lookup app", exc)
        else:
            app.add_log(message)
