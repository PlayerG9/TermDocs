#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import re
from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.rules_inline import StateInline
from mdit_py_plugins.front_matter import front_matter_plugin  # noqa
from mdit_py_plugins.attrs import attrs_plugin, attrs_block_plugin  # noqa
from mdit_py_plugins.footnote import footnote_plugin  # noqa
import mdit_py_plugins.attrs.parse


def emoji_plugin(md: MarkdownIt):
    md.inline.ruler.push(
        ruleName="emoji",
        fn=_emoji_rule,
    )


def _emoji_rule(state: StateInline, silent: bool):
    if state.src[state.pos] != ":":
        return False
    pos = state.pos + 1
    emoji_chars = []
    while pos < state.posMax:
        char = state.src[pos]
        pos += 1
        if char.isalnum():  # maybe change test
            emoji_chars.append(char)
        elif char == ":":
            break
        else:
            return False
    else:
        return False
    emoji_name = ''.join(emoji_chars)
    state.pos += len(emoji_name) + 2
    token = state.push(ttype="emoji", tag="", nesting=0)
    token.content = emoji_name
    # token.attrSet('emoji_name', emoji_name)
    token.markup = ":"

    return True


def toc_plugin(md: MarkdownIt):
    md.block.ruler.before(
        beforeName="list",
        ruleName="toc",
        fn=_toc_rule,
    )


__COMPLEX_TOC_RE = re.compile(r"(?P<style>[-*]|\d+\.) .+\n\{:toc}", re.IGNORECASE)


def _toc_rule(state: StateBlock, startLine: int, endLine: int, silent: bool):
    # no whitespace offset on the first line
    if state.tShift[startLine] != 0:
        return False

    pos = state.bMarks[startLine]
    end = state.eMarks[startLine]
    content = state.src[pos:end]

    if content.startswith('[[TOC]]'):
        state.line = startLine + 1
        token = state.push(ttype="toc", tag="", nesting=0)
        token.map = [startLine, state.line]
        token.attrs["style"] = "-"
        token.markup = '[['
        return True

    # also no whitespace offset on the second line
    if state.tShift[startLine+1] != 0:
        return False

    pos = state.bMarks[startLine]
    maximum = state.eMarks[startLine+1]
    content = state.src[pos:maximum]
    match = __COMPLEX_TOC_RE.fullmatch(content)

    if match is not None:
        state.line = startLine + 2
        token = state.push(ttype="toc", tag="", nesting=0)
        token.map = [startLine, state.line]
        token.attrs["style"] = match.group('style')
        token.markup = '{:'
        return True

    return False


attr_parse = mdit_py_plugins.attrs.parse


def new_handle_start(char: str, pos: int, _: attr_parse.TokenState) -> attr_parse.State:
    if pos == 0 and char == "{":
        return attr_parse.State.START
    if pos == 1 and char == ":":
        return attr_parse.State.SCANNING
    raise attr_parse.ParseError("Attributes must start with '{:'", pos)


attr_parse.HANDLERS[attr_parse.State.START] = new_handle_start
