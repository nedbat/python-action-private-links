import re
import sys
import textwrap

import lxml.html
import markdown2
import requests

# from https://github.com/trentm/python-markdown2/wiki/link-patterns
URL_PATTERN = re.compile(
    r"""
        \b
        (
            (?:https?://|(?<!//)www\.)    # prefix - https:// or www.
            \w[\w_\-]*(?:\.\w[\w_\-]*)*   # host
            [^<>\s"']*                    # rest of url
            (?<![?!.,:*_~);])             # exclude trailing punctuation
            (?=[?!.,:*_~);]?(?:[<\s]|$))  # make sure that we're not followed by " or ', i.e. we're outside of href="...".
        )
    """,
    re.X
)
markdown = markdown2.Markdown(
    extras=["link-patterns"],
    link_patterns=[(URL_PATTERN, r"\1")]
)

def stdin_commits():
    """Read rev-list output on stdin, yield (hash, commit-message) pairs."""
    commits = sys.stdin.read().split("\0")
    for commit in commits:
        if commit:
            meta, message = commit.split("\n\n", maxsplit=1)
            hash = meta.split("\n", maxsplit=1)[0]
            yield (hash, textwrap.dedent(message))

def things_to_check():
    """What are all of the things we should check?"""
    yield "PR title", sys.argv[1]
    yield "PR description", sys.argv[2]
    for hash, message in stdin_commits():
        yield f"commit {hash}", message

def markdown_urls(text):
    """Yield the URLs in the markdown `text`."""
    html = markdown.convert(text)
    doc = lxml.html.document_fromstring(html)
    for link in doc.xpath('//a'):
        yield link.get('href')

def text_errors(text):
    """Yield error messages for problems in `text`, maybe none."""
    for url in markdown_urls(text):
        try:
            status = requests.get(url).status_code
        except requests.RequestException as exc:
            yield f"URL {url} failed: {exc}"
        else:
            if not (200 <= status < 300):
                yield f"URL {url} status is {status}"

for name, text in things_to_check():
    for error_msg in text_errors(text):
        print(f"{name}: {error_msg}")
