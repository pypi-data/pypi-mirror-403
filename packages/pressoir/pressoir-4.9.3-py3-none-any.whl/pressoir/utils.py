import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import mistune
from jinja2.filters import do_forceescape, do_striptags
from slugify.slugify import slugify

from . import ROOT_DIR

html_comments_re = re.compile(r"<!--.*?-->")
html_tags_re = re.compile(r"<[^>]*>")


def strip_html_comments(value):
    if not value:
        return ""
    return html_comments_re.sub("", value)


def strip_html_tags(value):
    if not value:
        return ""
    return html_tags_re.sub("", value)


def raw_to_html(content: str) -> str:
    return str(mistune.html(content)).strip()[len("<p>") : -len("</p>")]


def html_to_stripped(content: str) -> str:
    return str(do_forceescape(do_striptags(raw_to_html(content))))


def add_raw_html_stripped_slug(obj: dataclass, key: str = "title") -> None:
    data_raw = getattr(obj, key)
    obj.__setattr__(f"{key}_raw", data_raw)
    data_html = raw_to_html(getattr(obj, f"{key}_raw"))
    obj.__setattr__(f"{key}_html", data_html)
    data_stripped = html_to_stripped(getattr(obj, f"{key}_html"))
    obj.__setattr__(f"{key}_stripped", data_stripped)
    data_slug = slugify(getattr(obj, f"{key}_stripped"))
    obj.__setattr__(f"{key}_slug", data_slug)


def get_template_path(repository_path, name):
    """Try to find it within the book folder, fallback on pressoir one."""
    template_path = repository_path / "templates" / name
    if not template_path.exists():
        template_path = ROOT_DIR / "templates" / name
    return template_path


def each_file_from(source_dir, pattern="*.html", exclude=None):
    """Walk across the `source_dir` and return the html file paths."""
    for path in _each_path_from(source_dir, pattern=pattern, exclude=exclude):
        if path.is_file():
            yield path


def each_folder_from(source_dir, exclude=None):
    """Walk across the `source_dir` and return the folder paths."""
    for path in _each_path_from(source_dir, exclude=exclude):
        if path.is_dir():
            yield path


def _each_path_from(source_dir, pattern="*", exclude=None):
    for path in sorted(Path(source_dir).glob(pattern)):
        if exclude is not None and path.name in exclude:
            continue
        yield path


def generate_md5(content):
    return hashlib.md5(content.encode()).hexdigest()


def neighborhood(iterable, first=None, last=None):
    """
    Yield the (index, previous, current, next) items given an iterable.

    You can specify a `first` and/or `last` item for bounds.
    """
    index = 1
    iterator = iter(iterable)
    previous = first
    current = next(iterator)  # Throws StopIteration if empty.
    for next_ in iterator:
        yield (index, previous, current, next_)
        previous = current
        index += 1
        current = next_
    yield (index, previous, current, last)
