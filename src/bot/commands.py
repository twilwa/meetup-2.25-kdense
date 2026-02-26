# ABOUTME: Parses Twitch chat messages for anime generation commands.
# ABOUTME: Extracts prompts from "!anime ..." messages, handling quoted and unquoted forms.

from __future__ import annotations


def parse_anime_command(message: str) -> str | None:
    """Extract the generation prompt from a chat message.

    Recognizes messages starting with ``!anime`` (case-insensitive).
    The prompt may be surrounded by double quotes or given as bare words.

    Args:
        message: Raw chat message text.

    Returns:
        The extracted prompt string, or ``None`` if the message is not a
        valid ``!anime`` command or the prompt is empty.

    Examples:
        >>> parse_anime_command('!anime "fire sword"')
        'fire sword'
        >>> parse_anime_command('!anime robot cat doing ballet')
        'robot cat doing ballet'
        >>> parse_anime_command('hey everyone!')
        None
        >>> parse_anime_command('!anime')
        None
    """
    # Check if message starts with !anime (case-insensitive)
    stripped = message.strip()
    if not stripped.lower().startswith("!anime"):
        return None

    # Remove the !anime prefix
    remainder = stripped[6:].strip()

    # Empty remainder means no prompt
    if not remainder:
        return None

    # Check for quoted prompt
    if remainder.startswith('"'):
        # Find the closing quote (not preceded by backslash)
        i = 1
        while i < len(remainder):
            if remainder[i] == '"' and remainder[i - 1] != '\\':
                # Found unescaped closing quote
                inner = remainder[1:i]
                # Unescape any escaped quotes
                inner = inner.replace('\\"', '"')
                return inner or None
            i += 1
        # No closing quote found, treat content after opening quote as unquoted
        return remainder[1:].strip() or None

    # Unquoted prompt - return all remaining words
    return remainder or None
