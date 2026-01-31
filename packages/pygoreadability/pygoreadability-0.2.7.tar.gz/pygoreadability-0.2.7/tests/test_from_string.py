import pytest

from pygoreadability import ReadabilityArticle, from_string


def test_from_string_accepts_null_bytes():
    html = """<!doctype html>
    <html>
      <head>
        <title>Null Byte Test</title>
      </head>
      <body>
        <p>Hello\x00World</p>
      </body>
    </html>
    """
    article = from_string(html, url="https://example.com")
    assert article.title == "Null Byte Test"


def test_from_string_basic_content():
    html = """<!doctype html>
    <html>
      <head>
        <title>Example</title>
      </head>
      <body>
        <article>
          <h1>Example</h1>
          <p>Hello World</p>
        </article>
      </body>
    </html>
    """
    article = from_string(html, url="https://example.com")
    assert isinstance(article, ReadabilityArticle)
    assert article.title == "Example"
    assert "Hello World" in article.content_text
    assert "<p>" in article.content_html


def test_from_string_without_url():
    html = """<!doctype html>
    <html>
      <head>
        <title>No URL</title>
      </head>
      <body>
        <p>Content</p>
      </body>
    </html>
    """
    article = from_string(html)
    assert article.title == "No URL"


def test_from_string_invalid_url():
    html = "<html><head><title>Bad URL</title></head><body><p>Test</p></body></html>"
    with pytest.raises(RuntimeError):
        from_string(html, url="http://[::1")
