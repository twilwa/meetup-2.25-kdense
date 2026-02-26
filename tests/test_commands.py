# ABOUTME: Tests for the Twitch chat command parser.
# ABOUTME: Verifies prompt extraction from !anime messages in all expected forms.

from src.bot.commands import parse_anime_command


class TestParseAnimeCommandQuoted:
    """Tests for quoted prompt extraction."""

    def test_quoted_prompt_extracts_content(self) -> None:
        """Quoted prompt like '!anime "girl with fire sword"' extracts inner text."""
        result = parse_anime_command('!anime "girl with fire sword"')
        assert result == "girl with fire sword"

    def test_quoted_prompt_with_escaped_quotes(self) -> None:
        r"""Prompt with escaped quotes like '!anime "prompt with \"escaped\" quotes"' preserves escapes."""
        result = parse_anime_command('!anime "prompt with \\"escaped\\" quotes"')
        assert result == 'prompt with "escaped" quotes'


class TestParseAnimeCommandUnquoted:
    """Tests for unquoted (bare word) prompt extraction."""

    def test_unquoted_prompt_extracts_all_words(self) -> None:
        """Unquoted prompt like '!anime robot cat doing ballet' joins all words."""
        result = parse_anime_command("!anime robot cat doing ballet")
        assert result == "robot cat doing ballet"


class TestParseAnimeCommandInvalid:
    """Tests for messages that are not valid !anime commands."""

    def test_non_command_message_returns_none(self) -> None:
        """Regular chat like 'hey everyone!' returns None."""
        result = parse_anime_command("hey everyone!")
        assert result is None

    def test_command_with_no_prompt_returns_none(self) -> None:
        """Bare '!anime' with no prompt returns None."""
        result = parse_anime_command("!anime")
        assert result is None

    def test_command_with_empty_quotes_returns_none(self) -> None:
        """Command '!anime ""' with empty quotes returns None."""
        result = parse_anime_command('!anime ""')
        assert result is None

    def test_command_with_whitespace_only_returns_none(self) -> None:
        """Command '!anime   ' with only whitespace returns None."""
        result = parse_anime_command("!anime   ")
        assert result is None


class TestParseAnimeCommandCaseInsensitive:
    """Tests for case-insensitive command matching."""

    def test_uppercase_command_extracts_prompt(self) -> None:
        """'!ANIME "prompt"' should work the same as lowercase."""
        result = parse_anime_command('!ANIME "prompt"')
        assert result == "prompt"

    def test_mixed_case_command_extracts_prompt(self) -> None:
        """'!Anime "prompt"' should work regardless of case."""
        result = parse_anime_command('!Anime "prompt"')
        assert result == "prompt"
