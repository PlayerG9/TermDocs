---
layout: default
title: Commonmark
parent: Markdown Features
nav_order: 1
---

# Commonmark

- TOC
{:toc}

## Headers

Headers levels 1 through 6 are supported.

### This is H3

This is H3 Content

#### This is H4

Header level 4 content. Drilling down in to finer headings.

##### This is H5

Header level 5 content.

###### This is H6

Header level 6 content.

## Typography

The usual Markdown typography is supported. The exact output depends on your terminal, although most are fairly consistent.

### Emphasis/Italic

Emphasis is rendered with `*asterisks*`, and looks *like this*;

### Strong/Bold

Use two asterisks to indicate strong which renders in bold, e.g. `**strong**` render **strong**.

### Inline code ###

Inline code is indicated by backticks. e.g. `import this`.

## Horizontal rule

Draw a horizontal rule with three dashes (`---`).

---

Good for natural breaks in the content, that don't require another header.

## Images

TermDocs supports most common image formats and also animated images like `.gif`
(with reduced framerate) and also vector graphics (`.svg`)

![Screenshot](assets/Screenshot-0.svg)

```markdown
![Screenshot](assets/Screenshot-0.svg)
```

## Ordered Lists

1. Lists can be ordered
1. Lists can be unordered
   1. I must not fear.
      1. Fear is the mind-killer.
         1. Fear is the little-death that brings total obliteration.
            1. I will face my fear.
         1. I will permit it to pass over me and through me.
      1. And when it has gone past, I will turn the inner eye to see its path.
   1. Where the fear has gone there will be nothing. Only I will remain.

## Unordered Lists

- Lists can be ordered
- Lists can be unordered
   - I must not fear.
      - Fear is the mind-killer.
         - Fear is the little-death that brings total obliteration.
            - I will face my fear.
         - I will permit it to pass over me and through me.
      - And when it has gone past, I will turn the inner eye to see its path.
   - Where the fear has gone there will be nothing. Only I will remain.


## Fences/Code-Blocks

```md
# Lorem Ipsum
Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren,
```

## Quote

Quotes are introduced with a chevron, and render like this:

> I must not fear.
> Fear is the mind-killer.
> Fear is the little-death that brings total obliteration.
> I will face my fear.
> I will permit it to pass over me and through me.
> And when it has gone past, I will turn the inner eye to see its path.
> Where the fear has gone there will be nothing. Only I will remain."

Quotes nest nicely. Here's what quotes within quotes look like:

> I must not fear.
> > Fear is the mind-killer.
> > Fear is the little-death that brings total obliteration.
> > I will face my fear.
> > > I will permit it to pass over me and through me.
> > > And when it has gone past, I will turn the inner eye to see its path.
> > > Where the fear has gone there will be nothing. Only I will remain.
