import re


def normalize_text(text: str) -> str:
    """
    Normalize plain text:
    - Join hyphenated line breaks: 'foo-\nbar' -> 'foobar'
    - Normalize Windows CRLF to LF
    - Collapse 3+ newlines to 2
    - Trim whitespace at line starts/ends
    - Strip leading/trailing whitespace
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()
