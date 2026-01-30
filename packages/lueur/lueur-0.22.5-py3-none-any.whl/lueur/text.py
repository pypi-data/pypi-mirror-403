from textwrap import dedent, wrap

__all__ = ["collapse"]


def collapse(text: str) -> str:
    """
    Collpase a multiline string into a single line string.
    """
    return " ".join(wrap(dedent(text))).strip()
