"""Core archiving logic."""

import time
from datetime import UTC, datetime
from pathlib import Path

from edapi import EdAPI
from rich.progress import Progress

from ed_archiver.models import CourseMetadata, Thread
from ed_archiver.transformer import transform_thread

MAX_RETRIES = 3
BASE_DELAY = 1.0  # Base delay between requests (seconds)


class Archiver:
    """Archives Ed courses to RAG-ready JSON files."""

    def __init__(
        self,
        ed_client: EdAPI,
        region: str,
        output_dir: Path = Path("out"),
    ) -> None:
        """Initialize archiver.

        Args:
            ed_client: Authenticated EdAPI client.
            region: Ed region code (e.g., "us", "eu", "au").
            output_dir: Base directory for output files.
        """
        self._ed = ed_client
        self._region = region
        self._output_dir = output_dir

    def archive_course(
        self,
        course_id: str,
        progress: Progress | None = None,
    ) -> Path:
        """Archive all threads from a course.

        Args:
            course_id: The Ed course ID to archive.
            progress: Optional rich Progress instance for display.

        Returns:
            Path to the course output directory.

        Raises:
            ValueError: If no threads are found in the course.
        """
        course_dir = self._output_dir / course_id
        threads_dir = course_dir / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        # Discover all thread IDs
        thread_ids = self._get_all_thread_ids(course_id, progress)

        if not thread_ids:
            raise ValueError(f"No threads found in course {course_id}")

        # Archive threads sequentially with rate limiting
        task = None
        if progress:
            task = progress.add_task("Archiving threads", total=len(thread_ids))

        failed = 0
        for thread_id in thread_ids:
            success = self._fetch_and_save_thread(thread_id, threads_dir, progress)
            if not success:
                failed += 1

            if progress and task is not None:
                progress.update(task, advance=1)

        # Write metadata
        self._write_metadata(course_dir, course_id, len(thread_ids) - failed)

        if failed > 0 and progress:
            progress.console.print(
                f"[yellow]Warning:[/] {failed} threads failed to archive"
            )

        return course_dir

    def _get_all_thread_ids(
        self,
        course_id: str,
        progress: Progress | None,
    ) -> list[int]:
        """Fetch all thread IDs from course.

        Args:
            course_id: The Ed course ID.
            progress: Optional rich Progress instance.

        Returns:
            List of all thread IDs in the course.
        """
        task = None
        if progress:
            task = progress.add_task("Discovering threads", total=None)

        thread_ids: list[int] = []
        offset = 0
        batch_size = 100

        while True:
            threads = self._ed.list_threads(course_id, limit=batch_size, offset=offset)
            if not threads:
                break

            thread_ids.extend(t["id"] for t in threads)
            offset += batch_size

            if progress and task is not None:
                progress.update(
                    task,
                    description=f"Discovering threads ({len(thread_ids)} found)",
                )

        if progress and task is not None:
            progress.remove_task(task)

        return thread_ids

    def _fetch_and_save_thread(
        self,
        thread_id: int,
        threads_dir: Path,
        progress: Progress | None,
    ) -> bool:
        """Fetch, transform, and save a single thread with retry.

        Args:
            thread_id: The thread ID to archive.
            threads_dir: Directory to save the thread JSON.
            progress: Optional progress instance for logging.

        Returns:
            True if successful, False if failed after retries.
        """
        delay = BASE_DELAY

        for attempt in range(MAX_RETRIES):
            try:
                raw = self._ed.get_thread(thread_id)

                transformed = transform_thread(raw)
                thread = Thread.model_validate(transformed)

                output_file = threads_dir / f"{thread_id}.json"
                output_file.write_text(
                    thread.model_dump_json(indent=2),
                    encoding="utf-8",
                )
                return True

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "rate_limit" in error_str

                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    # Rate limited - wait and retry
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                elif attempt < MAX_RETRIES - 1:
                    # Other error - brief pause and retry
                    time.sleep(0.5)
                else:
                    # Final attempt failed
                    if progress:
                        progress.console.print(
                            f"[yellow]Warning:[/] Thread {thread_id} failed: {e}"
                        )
                    return False

        return False

    def _write_metadata(
        self,
        course_dir: Path,
        course_id: str,
        thread_count: int,
    ) -> None:
        """Write course metadata file.

        Args:
            course_dir: Course output directory.
            course_id: The Ed course ID.
            thread_count: Total number of archived threads.
        """
        base_url = f"https://edstem.org/{self._region}/courses/{course_id}"

        metadata = CourseMetadata(
            course_id=course_id,
            region=self._region,
            archived_at=datetime.now(UTC),
            thread_count=thread_count,
            base_url=base_url,
        )

        output_file = course_dir / "metadata.json"
        output_file.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )
