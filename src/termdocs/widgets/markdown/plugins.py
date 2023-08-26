#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from mdit_py_plugins.front_matter import front_matter_plugin  # noqa


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
