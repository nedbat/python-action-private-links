import re
import sys

import lxml.html
import markdown2

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
    link_patterns=[(URL_PATTERN, r'\1')]
)

def stdin_commits():
    commits = sys.stdin.read().split("\0")
    for commit in commits:
        if commit:
            meta, message = commit.split("\n\n", maxsplit=1)
            hash = meta.split("\n", maxsplit=1)[0]
            yield (hash, message)

def markdown_urls(text):
    print(f"{text=}")
    html = markdown.convert(text)
    print(f"{html=}")
    doc = lxml.html.document_fromstring(html)
    for link in doc.xpath('//a'):
        yield link.get('href')

def things_to_check():
    yield "PR title", sys.argv[1]
    yield "PR description", sys.argv[2]
    for hash, message in stdin_commits():
        yield f"commit {hash}", message

for name, text in things_to_check():
    for url in markdown_urls(text):
        print(f"{name} has {url}")
