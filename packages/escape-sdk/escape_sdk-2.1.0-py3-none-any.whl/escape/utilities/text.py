"""Text manipulation utilities for RuneScape text."""

import re


def strip_color_tags(text: str) -> str:
    """Remove RuneScape color and image tags from text."""
    # Remove all tags in angle brackets (opening and closing)
    text = re.sub(r"<[^>]+>", "", text)
    return text
