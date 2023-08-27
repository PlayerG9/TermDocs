#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.rules_inline import StateInline
from mdit_py_plugins.front_matter import front_matter_plugin  # noqa
from mdit_py_plugins.attrs import attrs_plugin, attrs_block_plugin  # noqa
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
        beforeName="paragraph",
        ruleName="toc",
        fn=_toc_rule,
    )


def _toc_rule(state: StateBlock, startLine: int, endLine: int, silent: bool):
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]
    content = state.src[pos:maximum]

    if content not in {'[[TOC]]', '{:TOC}'}:
        return False

    state.line = startLine + 1

    token = state.push(ttype="toc", tag="", nesting=0)
    token.map = [startLine, state.line]
    token.markup = content[:2]

    return True


# def toc_plugin(md: MarkdownIt):
#     md.inline.ruler.push(
#         ruleName="toc",
#         fn=_toc_rule,
#     )
#
#
# def _toc_rule(state: StateInline, silent: bool):
#     if state.src not in {'[[TOC]]', '{:TOC}'}:
#         return False
#
#     state.pos += len(state.src)
#     token = state.push(ttype="toc", tag="", nesting=0)
#     token.markup = state.src[:2]
#
#     return True


attr_parse = mdit_py_plugins.attrs.parse


def new_handle_start(char: str, pos: int, _: attr_parse.TokenState) -> attr_parse.State:
    if pos == 0 and char == "{":
        return attr_parse.State.START
    if pos == 1 and char == ":":
        return attr_parse.State.SCANNING
    raise attr_parse.ParseError("Attributes must start with '{:'", pos)


attr_parse.HANDLERS[attr_parse.State.START] = new_handle_start
