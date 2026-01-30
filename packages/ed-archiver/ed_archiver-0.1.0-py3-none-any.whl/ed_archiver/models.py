"""Pydantic models for RAG-ready thread schema."""

from datetime import datetime

from pydantic import BaseModel


class Comment(BaseModel):
    """A comment on an answer."""

    id: int
    content: str
    images: list[str] = []
    links: list[str] = []
    vote_count: int
    is_endorsed: bool
    created_at: datetime


class Answer(BaseModel):
    """An answer to a thread."""

    id: int
    content: str
    images: list[str] = []
    links: list[str] = []
    vote_count: int
    is_endorsed: bool
    is_accepted: bool
    created_at: datetime
    comments: list[Comment] = []


class Thread(BaseModel):
    """A discussion thread, RAG-ready."""

    id: int
    type: str
    title: str
    category: str
    subcategory: str
    created_at: datetime
    is_answered: bool
    is_pinned: bool
    is_endorsed: bool
    vote_count: int
    view_count: int
    reply_count: int
    content: str
    images: list[str] = []
    links: list[str] = []
    answers: list[Answer] = []
    full_text: str


class CourseMetadata(BaseModel):
    """Metadata about an archived course."""

    course_id: str
    region: str
    archived_at: datetime
    thread_count: int
    base_url: str  # e.g., "https://edstem.org/eu/courses/1124"
