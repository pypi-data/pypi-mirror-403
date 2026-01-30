"""Tests for URL/ID parser."""

import pytest

from ed_archiver.parser import EdUrl, parse_input


class TestParseInput:
    """Tests for parse_input function."""

    def test_plain_course_id(self) -> None:
        result = parse_input("1124")
        assert result == EdUrl(course_id="1124", region="us")

    def test_course_id_with_whitespace(self) -> None:
        result = parse_input("  1124  ")
        assert result == EdUrl(course_id="1124", region="us")

    def test_full_url_eu(self) -> None:
        result = parse_input("https://edstem.org/eu/courses/1124/discussion/")
        assert result == EdUrl(course_id="1124", region="eu")

    def test_full_url_us(self) -> None:
        result = parse_input("https://edstem.org/us/courses/23247/discussion/")
        assert result == EdUrl(course_id="23247", region="us")

    def test_full_url_au(self) -> None:
        result = parse_input("https://edstem.org/au/courses/999/discussion/")
        assert result == EdUrl(course_id="999", region="au")

    def test_partial_url(self) -> None:
        result = parse_input("edstem.org/eu/courses/1124")
        assert result == EdUrl(course_id="1124", region="eu")

    def test_invalid_input(self) -> None:
        with pytest.raises(ValueError, match="Invalid input"):
            parse_input("not-a-course")

    def test_empty_input(self) -> None:
        with pytest.raises(ValueError, match="Invalid input"):
            parse_input("")
