# Ed Archiver: RAG-Ready Restructure

**Date:** 2026-01-25
**Status:** Approved

## Goal

Transform ed-archiver from a simple JSON dumper into a clean Python package that outputs RAG-optimized JSON files with proper structure, metadata, and region support.

## Output Structure

```
out/{course_id}/
├── metadata.json
└── threads/
    └── {thread_id}.json
```

## Thread Schema

```json
{
  "id": 98897,
  "type": "question",
  "title": "Link for the recorded lessons",
  "category": "General",
  "subcategory": "",
  "created_at": "2024-03-27T20:33:03Z",
  "is_answered": true,
  "is_pinned": false,
  "is_endorsed": false,
  "vote_count": 0,
  "view_count": 219,
  "reply_count": 3,
  "content": "Hello,\n\nI was under the impression...",
  "answers": [
    {
      "id": 185874,
      "content": "Maybe you're talking about this: https://...",
      "vote_count": 0,
      "is_endorsed": false,
      "is_accepted": true,
      "created_at": "2024-03-27T21:19:56Z",
      "comments": [
        {
          "id": 186147,
          "content": "Yes, that is it. Thank you!",
          "vote_count": 0,
          "is_endorsed": false,
          "created_at": "2024-03-28T03:36:35Z"
        }
      ]
    }
  ],
  "full_text": "Link for the recorded lessons\n\nHello, I was under the impression...\n\n---\n\nMaybe you're talking about this: https://..."
}
```

### Fields Kept (useful for RAG filtering/ranking)

| Field | Purpose |
|-------|---------|
| `vote_count` | Quality signal |
| `view_count` | Popularity signal |
| `is_answered`, `is_endorsed` | Quality markers |
| `is_pinned` | Importance signal |
| `category`, `subcategory` | Filtering |
| `type` | question vs announcement vs discussion |
| `created_at` | Recency |
| `reply_count` | Engagement signal |

### Fields Stripped (noise for RAG)

- `user_id`, `anonymous_id`, `editor_id` - privacy + useless
- `course_id` - redundant (in folder path)
- `is_seen`, `is_starred`, `glanced_at` - user-session state
- `flag_count` - moderation internal
- `content` (XML) - use `document` (plain text) instead

### Fields Added

- `full_text`: Concatenated title + question + answers for single-field embedding
- `is_accepted`: Boolean on answers (derived from thread's `accepted_id`)

## Package Structure

```
ed-archiver/
├── pyproject.toml
├── README.md
├── .env.sample
│
├── src/
│   └── ed_archiver/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── client.py
│       ├── archiver.py
│       ├── transformer.py
│       ├── parser.py
│       └── models.py
│
└── out/
```

## pyproject.toml

```toml
[project]
name = "ed-archiver"
version = "0.1.0"
description = "Archive Ed Discussion courses into RAG-ready JSON"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "edapi>=0.1.0",
    "pydantic>=2.0",
    "rich>=13.0",
]

[project.scripts]
ed-archiver = "ed_archiver.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ed_archiver"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.4",
]
```

## CLI Usage

```bash
ed-archiver                                    # Interactive mode
ed-archiver 1255                               # Direct course ID (defaults to US)
ed-archiver https://edstem.org/eu/courses/1124 # Full URL with region
ed-archiver 1255 -o ./data                     # Custom output dir
```

## Region Support

The CLI accepts full Ed URLs and extracts the region:

- `edstem.org/eu/courses/1124` → API: `eu.edstem.org/api/`
- `edstem.org/us/courses/23247` → API: `us.edstem.org/api/`

Since `edapi` hardcodes the base URL, we patch the module constants before instantiation:

```python
import edapi.edapi as edapi_module

def create_client(region: str) -> EdAPI:
    if region == "us":
        subdomain = ""
    else:
        subdomain = f"{region}."

    edapi_module.API_BASE_URL = f"https://{subdomain}edstem.org/api/"
    edapi_module.STATIC_FILE_BASE_URL = f"https://static.{subdomain}edusercontent.com/files/"

    return EdAPI()
```

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Argument parsing, user prompts, progress display |
| `client.py` | EdAPI instantiation with region support |
| `parser.py` | Parse course ID or URL input |
| `archiver.py` | Orchestrates fetching and saving threads |
| `transformer.py` | Raw Ed API data → clean schema |
| `models.py` | Pydantic models for type-safe serialization |

## Implementation Tasks

1. Create `src/ed_archiver/` package structure
2. Implement `models.py` with Pydantic models
3. Implement `parser.py` for URL/ID parsing
4. Implement `client.py` for region-aware EdAPI
5. Implement `transformer.py` for data transformation
6. Implement `archiver.py` for orchestration
7. Implement `cli.py` with rich progress
8. Update `pyproject.toml`
9. Update README.md
10. Test with real course
