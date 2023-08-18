#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
from textual.logging import active_app


class InternLoggingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        """Invoked by logging."""
        message = self.format(record)
        try:
            app = active_app.get()
        except LookupError as exc:
            print("Failed to lookup app", exc)
        else:
            app.add_log(message)


class SpecialModuleLoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == "root"
