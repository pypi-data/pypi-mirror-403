"""Parse course ID or full Ed URL."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EdUrl:
    """Parsed Ed Discussion URL."""

    course_id: str
    region: str  # "us", "eu", "au", etc.


def parse_input(value: str) -> EdUrl:
    """Parse course ID or full Ed URL.

    Accepts:
        - "1124"
        - "https://edstem.org/eu/courses/1124/discussion/"
        - "edstem.org/us/courses/23247"

    Returns:
        EdUrl with course_id and region extracted.

    Raises:
        ValueError: If input cannot be parsed.
    """
    value = value.strip()

    # Try URL pattern first
    pattern = r"edstem\.org/(\w+)/courses/(\d+)"
    match = re.search(pattern, value)

    if match:
        region, course_id = match.groups()
        return EdUrl(course_id=course_id, region=region)

    # Fallback: plain course ID (default to US)
    if value.isdigit():
        return EdUrl(course_id=value, region="us")

    raise ValueError(f"Invalid input: {value!r}. Expected course ID or Ed URL.")
