---
layout: default
title: Custom Features
parent: Markdown Features
nav_order: 3
---

# Custom/Uncommon Markdown Features

- TOC
{:toc}

## Table of Contents

To add a TOC use one of the following 

```markdown
[[TOC]]

- TOC
{:toc}

1. TOC
{:toc}
```

You can also adjust the depth of a TOC by setting the depth

{: depth=1 }
{:TOC}

```markdown
{: depth=1 }
[[TOC]]
```

### Visible Heading

### Invisible Heading
{: .no_toc }

And hide headers by adding the `no-toc` class

```markdown
{: .no_toc }
### Invisible Heading
```

## Attributes

{: .note }
> By default, no classes are loaded.
> Start TermDocs with the `--md-css` option to load default styles (e.g. `.warning`, `.text-right`)
> or with `--css [file]` for custom classes.
> (Note: this feature is disabled because it increases the starting time significantly)

### Block Level Attributes

{: .warning }
> Quote with different background color

```markdown
{: .warning }
> Quote with different background color
```

### Inline Attributes

{: .warning }
> Not quite functional yet

Inline `attributes`{: .italic } can be added

```markdown
Inline `attributes`{: .italic } can be added
```

## Footnotes

Here is a footnote reference,[^1] and another.[^longnote]

[^1]: Here is the footnote.

[^longnote]: Here's one with multiple blocks.
    Subsequent paragraphs are indented to show that they
belong to the previous footnote.

```
Here is a footnote reference,[^1] and another.[^longnote]

[^1]: Here is the footnote.

[^longnote]: Here's one with multiple blocks.
    Subsequent paragraphs are indented to show that they
belong to the previous footnote.
```
