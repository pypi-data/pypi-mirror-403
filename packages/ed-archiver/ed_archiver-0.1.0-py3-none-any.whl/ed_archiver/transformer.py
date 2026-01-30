"""Transform raw Ed API responses to RAG-ready format."""

import re
from typing import Any


def _extract_images(xml_content: str) -> list[str]:
    """Extract image URLs from Ed XML content.

    Args:
        xml_content: Raw XML content from Ed API.

    Returns:
        List of image URLs found in the content.
    """
    if not xml_content:
        return []

    # Match <image src="..."/> tags
    pattern = r'<image[^>]+src="([^"]+)"'
    return re.findall(pattern, xml_content)


def _extract_links(xml_content: str) -> list[str]:
    """Extract link URLs from Ed XML content.

    Args:
        xml_content: Raw XML content from Ed API.

    Returns:
        List of link URLs found in the content.
    """
    if not xml_content:
        return []

    # Match <link href="...">...</link> tags
    pattern = r'<link[^>]+href="([^"]+)"'
    return re.findall(pattern, xml_content)


def transform_thread(raw: dict[str, Any]) -> dict[str, Any]:
    """Transform raw Ed API thread to RAG-ready format.

    Args:
        raw: Raw thread data from Ed API.

    Returns:
        Cleaned thread dict matching the Thread model schema.
    """
    accepted_id = raw.get("accepted_id")
    answers = [transform_answer(a, accepted_id) for a in raw.get("answers", [])]

    thread_content = raw.get("document", "")
    xml_content = raw.get("content", "")
    title = raw.get("title", "")

    return {
        "id": raw["id"],
        "type": raw.get("type", ""),
        "title": title,
        "category": raw.get("category", ""),
        "subcategory": raw.get("subcategory", ""),
        "created_at": raw["created_at"],
        "is_answered": raw.get("is_answered", False),
        "is_pinned": raw.get("is_pinned", False),
        "is_endorsed": raw.get("is_endorsed", False),
        "vote_count": raw.get("vote_count", 0),
        "view_count": raw.get("view_count", 0),
        "reply_count": raw.get("reply_count", 0),
        "content": thread_content,
        "images": _extract_images(xml_content),
        "links": _extract_links(xml_content),
        "answers": answers,
        "full_text": _build_full_text(title, thread_content, answers),
    }


def transform_answer(raw: dict[str, Any], accepted_id: int | None) -> dict[str, Any]:
    """Transform raw Ed API answer to RAG-ready format.

    Args:
        raw: Raw answer data from Ed API.
        accepted_id: The ID of the accepted answer for the thread, if any.

    Returns:
        Cleaned answer dict matching the Answer model schema.
    """
    xml_content = raw.get("content", "")

    return {
        "id": raw["id"],
        "content": raw.get("document", ""),
        "images": _extract_images(xml_content),
        "links": _extract_links(xml_content),
        "vote_count": raw.get("vote_count", 0),
        "is_endorsed": raw.get("is_endorsed", False),
        "is_accepted": raw["id"] == accepted_id if accepted_id else False,
        "created_at": raw["created_at"],
        "comments": [transform_comment(c) for c in raw.get("comments", [])],
    }


def transform_comment(raw: dict[str, Any]) -> dict[str, Any]:
    """Transform raw Ed API comment to RAG-ready format.

    Args:
        raw: Raw comment data from Ed API.

    Returns:
        Cleaned comment dict matching the Comment model schema.
    """
    xml_content = raw.get("content", "")

    return {
        "id": raw["id"],
        "content": raw.get("document", ""),
        "images": _extract_images(xml_content),
        "links": _extract_links(xml_content),
        "vote_count": raw.get("vote_count", 0),
        "is_endorsed": raw.get("is_endorsed", False),
        "created_at": raw["created_at"],
    }


def _build_full_text(
    title: str,
    content: str,
    answers: list[dict[str, Any]],
) -> str:
    """Concatenate title + content + answers for embedding.

    Args:
        title: Thread title.
        content: Thread content (plain text).
        answers: List of transformed answers.

    Returns:
        Single string with all text concatenated, suitable for embedding.
    """
    parts = [title, "", content]

    for answer in answers:
        parts.append("\n---\n")
        parts.append(answer["content"])

        # Include comments in full text
        for comment in answer.get("comments", []):
            parts.append("\n")
            parts.append(comment["content"])

    return "\n".join(parts)
