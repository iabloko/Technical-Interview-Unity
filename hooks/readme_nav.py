"""MkDocs hooks.

on_config: навигация сайта строится из docs/README.md.
    `### <раздел>` -> раздел, `- [<название>](<путь>.md)` -> страница раздела.
on_page_markdown: проверка конструкций, которые GitHub и Python-Markdown разбирают по-разному.
"""

import logging
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.readme_nav")

SECTION = re.compile(r"^###\s+(.+?)\s*$")
PAGE = re.compile(r"^-\s+\[(.+)\]\((.+?\.md)\)\s*$")

LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")
FENCE = re.compile(r"^\s*(>\s?)*\s*```")
QUOTE_PREFIX = re.compile(r"^\s*(>\s?)*")
SHALLOW_INDENT = re.compile(r"^ {1,3}\S")


def on_config(config):
    readme = Path(config.docs_dir) / "README.md"
    nav = [{"Главная": "README.md"}]
    target = nav
    for line in readme.read_text(encoding="utf-8").splitlines():
        if m := SECTION.match(line):
            target = []
            nav.append({m.group(1): target})
        elif m := PAGE.match(line):
            target.append({m.group(1): m.group(2)})
    config.nav = nav
    return config


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    in_fence = in_list = after_fence = False
    prev = ""
    for n, line in enumerate(markdown.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            after_fence = not in_fence
        elif not in_fence:
            if after_fence and QUOTE_PREFIX.sub("", line).strip():
                log.warning(f"{src}:{n}: текст сразу после закрывающего ```; нужна пустая строка")
            after_fence = False
            if SHALLOW_INDENT.match(line):
                log.warning(f"{src}:{n}: отступ 1-3 пробела; вложенное содержимое пункта списка — 4 пробела")
            if not line.strip():
                in_list = False
            elif LIST_ITEM.match(line):
                if prev.strip() and not in_list and not prev.lstrip().startswith("#"):
                    log.warning(f"{src}:{n}: список сразу после текста; нужна пустая строка перед списком")
                in_list = True
        prev = line
    return markdown
