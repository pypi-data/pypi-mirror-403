from __future__ import annotations

import ctypes
import importlib.resources
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReadabilityArticle:
    title: str
    byline: str
    excerpt: str
    site_name: str
    image_url: str
    favicon: str
    language: str
    published_time: str
    modified_time: str
    content_html: str
    content_text: str


class _CReadabilityArticle(ctypes.Structure):
    _fields_ = [
        ("title", ctypes.c_void_p),
        ("title_len", ctypes.c_int),
        ("byline", ctypes.c_void_p),
        ("byline_len", ctypes.c_int),
        ("excerpt", ctypes.c_void_p),
        ("excerpt_len", ctypes.c_int),
        ("site_name", ctypes.c_void_p),
        ("site_name_len", ctypes.c_int),
        ("image_url", ctypes.c_void_p),
        ("image_url_len", ctypes.c_int),
        ("favicon", ctypes.c_void_p),
        ("favicon_len", ctypes.c_int),
        ("language", ctypes.c_void_p),
        ("language_len", ctypes.c_int),
        ("published_time", ctypes.c_void_p),
        ("published_time_len", ctypes.c_int),
        ("modified_time", ctypes.c_void_p),
        ("modified_time_len", ctypes.c_int),
        ("content_html", ctypes.c_void_p),
        ("content_html_len", ctypes.c_int),
        ("content_text", ctypes.c_void_p),
        ("content_text_len", ctypes.c_int),
        ("error", ctypes.c_void_p),
        ("error_len", ctypes.c_int),
    ]


def _load_library() -> ctypes.CDLL:
    pkg = importlib.resources.files("pygoreadability")
    candidates = []
    for base in (
        pkg,
        pkg / ".dylibs",
        pkg.parent / "pygoreadability.libs",
    ):
        candidates.extend(
            [
                base / "libgoreadability.dylib",
                base / "libgoreadability.so",
            ]
        )
    for path in candidates:
        if path.is_file():
            return ctypes.CDLL(os.fspath(path))

    if os.environ.get("PYGOREADABILITY_AUTO_BUILD", "1") == "1":
        root = Path(__file__).resolve().parent.parent
        build_script = root / "scripts" / "build_lib.sh"
        if build_script.is_file():
            subprocess.check_call(["bash", os.fspath(build_script)], cwd=os.fspath(root))
            for path in candidates:
                if path.is_file():
                    return ctypes.CDLL(os.fspath(path))

    searched = ", ".join(os.fspath(p) for p in candidates)
    raise RuntimeError(
        "libgoreadability shared library not found in package. "
        f"Searched: {searched}"
    )


_LIB = _load_library()
_LIB.FromString.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
_LIB.FromString.restype = ctypes.POINTER(_CReadabilityArticle)
_LIB.FreeArticle.argtypes = [ctypes.POINTER(_CReadabilityArticle)]
_LIB.FreeArticle.restype = None


def _decode(ptr: Optional[int], length: int) -> str:
    if not ptr or length <= 0:
        return ""
    data = ctypes.string_at(ptr, length)
    return data.decode("utf-8", errors="replace")


def from_string(html: str, url: Optional[str] = None) -> ReadabilityArticle:
    if not isinstance(html, str):
        raise TypeError("html must be a str")
    if url is not None and not isinstance(url, str):
        raise TypeError("url must be a str or None")

    html_bytes = html.encode("utf-8")
    html_buf = ctypes.create_string_buffer(html_bytes)
    html_len = len(html_bytes)

    url_buf = None
    url_len = 0
    if url:
        url_bytes = url.encode("utf-8")
        url_buf = ctypes.create_string_buffer(url_bytes)
        url_len = len(url_bytes)

    ptr = _LIB.FromString(html_buf, html_len, url_buf, url_len)
    if not ptr:
        raise RuntimeError("FromString returned null pointer")

    try:
        article = ptr.contents
        err = _decode(article.error, article.error_len)
        if err:
            raise RuntimeError(err)
        return ReadabilityArticle(
            title=_decode(article.title, article.title_len),
            byline=_decode(article.byline, article.byline_len),
            excerpt=_decode(article.excerpt, article.excerpt_len),
            site_name=_decode(article.site_name, article.site_name_len),
            image_url=_decode(article.image_url, article.image_url_len),
            favicon=_decode(article.favicon, article.favicon_len),
            language=_decode(article.language, article.language_len),
            published_time=_decode(article.published_time, article.published_time_len),
            modified_time=_decode(article.modified_time, article.modified_time_len),
            content_html=_decode(article.content_html, article.content_html_len),
            content_text=_decode(article.content_text, article.content_text_len),
        )
    finally:
        _LIB.FreeArticle(ptr)
