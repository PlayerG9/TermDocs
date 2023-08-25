---
title: Getting-Started
layout: default
#has_children: true
---

{: .warning }
> This whole section has to be written

# Getting Started

<sup>something along</sup>

## Dependencies

> bash
> {: .label }
> git/wget/curl
> {: .label }
> python3 (3.7+)
> {: .label }
> python-pip
> {: .label }
> python-venv
> {: .label }

## Getting the Repository 

Select one of the following

```bash
git clone https://github.com/PlayerG9/TermDocs.git
```
```bash
wget -q https://github.com/PlayerG9/TermDocs/archive/refs/heads/main.zip && unzip -q main.zip && rm main.zip && mv TermDocs-main TermDocs
```
```bash
curl -sLJo main.zip https://github.com/PlayerG9/TermDocs/archive/refs/heads/main.zip && unzip -q main.zip && rm main.zip && mv TermDocs-main TermDocs
```

## Project Setup

```bash
cd TermDocs
python3 -m venv .venv
./.venv/bin/pip3 install -U pip 
./.venv/bin/pip3 install -U -r requirements.txt 
```
<sup>Commands my vary slightly depending on the Operating System used. These commands are for linux</sup>
