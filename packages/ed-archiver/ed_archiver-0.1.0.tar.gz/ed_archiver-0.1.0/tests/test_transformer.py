"""Tests for data transformer."""

from ed_archiver.transformer import (
    _extract_images,
    _extract_links,
    transform_comment,
    transform_thread,
)


class TestExtractImages:
    """Tests for image extraction from XML."""

    def test_single_image(self) -> None:
        xml = '<document><image src="https://example.com/img.png"/></document>'
        assert _extract_images(xml) == ["https://example.com/img.png"]

    def test_multiple_images(self) -> None:
        xml = '<image src="https://a.com/1.png"/><image src="https://b.com/2.png"/>'
        assert _extract_images(xml) == ["https://a.com/1.png", "https://b.com/2.png"]

    def test_no_images(self) -> None:
        xml = "<document><paragraph>No images here</paragraph></document>"
        assert _extract_images(xml) == []

    def test_empty_content(self) -> None:
        assert _extract_images("") == []
        assert _extract_images(None) == []  # type: ignore[arg-type]

    def test_image_with_attributes(self) -> None:
        xml = '<image src="https://example.com/img.png" width="100" height="50"/>'
        assert _extract_images(xml) == ["https://example.com/img.png"]


class TestExtractLinks:
    """Tests for link extraction from XML."""

    def test_single_link(self) -> None:
        xml = '<link href="https://example.com">Example</link>'
        assert _extract_links(xml) == ["https://example.com"]

    def test_multiple_links(self) -> None:
        xml = '<link href="https://a.com">A</link><link href="https://b.com">B</link>'
        assert _extract_links(xml) == ["https://a.com", "https://b.com"]

    def test_no_links(self) -> None:
        xml = "<document><paragraph>No links here</paragraph></document>"
        assert _extract_links(xml) == []


class TestTransformComment:
    """Tests for comment transformation."""

    def test_basic_comment(self) -> None:
        raw = {
            "id": 123,
            "document": "Thanks!",
            "content": "<document>Thanks!</document>",
            "vote_count": 1,
            "is_endorsed": False,
            "created_at": "2024-01-01T00:00:00Z",
        }
        result = transform_comment(raw)

        assert result["id"] == 123
        assert result["content"] == "Thanks!"
        assert result["vote_count"] == 1
        assert result["is_endorsed"] is False
        assert result["images"] == []
        assert result["links"] == []


class TestTransformThread:
    """Tests for thread transformation."""

    def test_basic_thread(self) -> None:
        raw = {
            "id": 456,
            "type": "question",
            "title": "How to X?",
            "category": "Homework",
            "subcategory": "",
            "created_at": "2024-01-01T00:00:00Z",
            "is_answered": True,
            "is_pinned": False,
            "is_endorsed": False,
            "vote_count": 5,
            "view_count": 100,
            "reply_count": 2,
            "document": "How do I do X?",
            "content": "<document>How do I do X?</document>",
            "answers": [],
        }
        result = transform_thread(raw)

        assert result["id"] == 456
        assert result["type"] == "question"
        assert result["title"] == "How to X?"
        assert result["content"] == "How do I do X?"
        assert result["is_answered"] is True
        assert "full_text" in result

    def test_thread_with_images(self) -> None:
        raw = {
            "id": 789,
            "type": "question",
            "title": "See image",
            "category": "General",
            "subcategory": "",
            "created_at": "2024-01-01T00:00:00Z",
            "is_answered": False,
            "is_pinned": False,
            "is_endorsed": False,
            "vote_count": 0,
            "view_count": 10,
            "reply_count": 0,
            "document": "Check this:",
            "content": '<document><image src="https://example.com/img.png"/></document>',
            "answers": [],
        }
        result = transform_thread(raw)

        assert result["images"] == ["https://example.com/img.png"]
