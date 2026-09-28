"""MkDocs hook: аудиоплеер на странице заметки.

Файл docs/<раздел>/audio/<заметка>.mp3 -> <audio> под заголовком страницы docs/<раздел>/<заметка>.md.
"""

import logging
import posixpath

log = logging.getLogger("mkdocs.hooks.audio")


def on_files(files, config):
    for file in files:
        folder, name = posixpath.split(file.src_uri)
        if posixpath.basename(folder) == "audio" and name.endswith(".mp3"):
            note = posixpath.join(posixpath.dirname(folder), name[: -len(".mp3")] + ".md")
            if files.get_file_from_path(note) is None:
                log.warning(f"{file.src_uri}: нет заметки {note}")
    return files


def on_page_content(html, page, config, files):
    folder, name = posixpath.split(page.file.src_uri)
    audio = files.get_file_from_path(posixpath.join(folder, "audio", posixpath.splitext(name)[0] + ".mp3"))
    if audio is None:
        return html
    player = f'<audio controls preload="metadata" src="{audio.url_relative_to(page.file)}" style="width: 100%"></audio>'
    return html.replace("</h1>", "</h1>\n" + player, 1)
