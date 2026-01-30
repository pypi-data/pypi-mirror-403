#!/usr/bin/env python3
"""
ASVS Drift Detector Tool

Compares local ASVS implementation against the latest upstream standard
to help teams manage drift and identify updates.

ASVS Requirements Addressed:
- V15.1.2: Maintain requirement inventory catalog (facilitates version tracking)
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.request import urlopen
from urllib.error import URLError


# --- Constants ---

UPSTREAM_ASVS_URL = (
    "https://raw.githubusercontent.com/OWASP/ASVS/master/5.0/docs_en/OWASP%20Application%20Security%20Verification%20Standard%205.0-en.json"
)

DEFAULT_LOCAL_PATH = "01-ASVS-Core-Reference/ASVS-5.0-en.json"


# --- Data Classes ---

@dataclass
class Requirement:
    """Represents a single ASVS requirement."""
    req_id: str
    description: str
    level: str
    chapter_id: str = ""
    chapter_name: str = ""
    section_id: str = ""
    section_name: str = ""

    def __hash__(self) -> int:
        return hash(self.req_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requirement):
            return False
        return self.req_id == other.req_id


@dataclass
class DriftResult:
    """Results of comparing local vs upstream ASVS."""
    added: list[Requirement] = field(default_factory=list)
    removed: list[Requirement] = field(default_factory=list)
    modified: list[tuple[Requirement, Requirement]] = field(default_factory=list)
    local_hash: str = ""
    upstream_hash: str = ""
    local_count: int = 0
    upstream_count: int = 0

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.modified:
            parts.append(f"{len(self.modified)} modified")
        return ", ".join(parts) if parts else "No drift detected"


# --- Protocols for Dependency Injection ---

class FileReader(Protocol):
    """Protocol for reading file contents."""
    def read(self, path: Path) -> str: ...


class UrlFetcher(Protocol):
    """Protocol for fetching URL contents."""
    def fetch(self, url: str) -> str: ...


# --- Concrete Implementations ---

class DefaultFileReader:
    """Default file reader implementation."""

    def read(self, path: Path) -> str:
        """Read file contents with UTF-8 encoding."""
        return path.read_text(encoding="utf-8")


class DefaultUrlFetcher:
    """Default URL fetcher using urllib."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        """Fetch URL contents."""
        try:
            with urlopen(url, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except URLError as e:
            raise ConnectionError(f"Failed to fetch {url}: {e}")


# --- Requirement Parsing ---

class RequirementParser:
    """Parses ASVS requirements from various JSON formats."""

    def parse(self, content: str) -> list[Requirement]:
        """Parse requirements from JSON content."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if isinstance(data, list):
            return self._parse_flat_format(data)
        elif isinstance(data, dict):
            return self._parse_nested_format(data)
        else:
            raise ValueError(f"Unexpected JSON structure: {type(data).__name__}")

    def _parse_flat_format(self, data: list[dict[str, Any]]) -> list[Requirement]:
        """Parse flat array format (used by local JSON files)."""
        requirements = []
        for item in data:
            if not isinstance(item, dict):
                continue
            req = Requirement(
                req_id=str(item.get("req_id", item.get("Shortcode", ""))),
                description=str(item.get("req_description", item.get("Description", ""))),
                level=str(item.get("L", item.get("Level", ""))),
                chapter_id=str(item.get("chapter_id", item.get("Chapter", ""))),
                chapter_name=str(item.get("chapter_name", item.get("ChapterName", ""))),
                section_id=str(item.get("section_id", item.get("Section", ""))),
                section_name=str(item.get("section_name", item.get("SectionName", ""))),
            )
            if req.req_id:
                requirements.append(req)
        return requirements

    def _parse_nested_format(self, data: dict[str, Any]) -> list[Requirement]:
        """Parse nested format (used by upstream OWASP JSON)."""
        requirements = []

        chapters = data.get("requirements", data.get("chapters", []))
        if not chapters and "Name" in data:
            chapters = [data]

        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue

            chapter_id = str(chapter.get("Shortcode", chapter.get("chapter_id", "")))
            chapter_name = str(chapter.get("Name", chapter.get("chapter_name", "")))

            items = chapter.get("Items", chapter.get("sections", []))
            for section in items:
                if not isinstance(section, dict):
                    continue

                section_id = str(section.get("Shortcode", section.get("section_id", "")))
                section_name = str(section.get("Name", section.get("section_name", "")))

                reqs = section.get("Items", section.get("requirements", []))
                for req_data in reqs:
                    if not isinstance(req_data, dict):
                        continue

                    req = Requirement(
                        req_id=str(req_data.get("Shortcode", req_data.get("req_id", ""))),
                        description=str(req_data.get("Description", req_data.get("req_description", ""))),
                        level=str(req_data.get("L1", {}).get("Required", "") or
                                  req_data.get("L2", {}).get("Required", "") or
                                  req_data.get("L3", {}).get("Required", "") or
                                  req_data.get("L", "")),
                        chapter_id=chapter_id,
                        chapter_name=chapter_name,
                        section_id=section_id,
                        section_name=section_name,
                    )
                    if req.req_id:
                        requirements.append(req)

        if not requirements:
            return self._parse_flat_format(
                data.get("requirements", data.get("Items", []))
            )

        return requirements


# --- Drift Detection ---

class DriftDetector:
    """Detects drift between local and upstream ASVS requirements."""

    def __init__(
        self,
        file_reader: FileReader,
        url_fetcher: UrlFetcher,
        parser: RequirementParser,
    ):
        self.file_reader = file_reader
        self.url_fetcher = url_fetcher
        self.parser = parser

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def load_local(self, path: Path) -> tuple[list[Requirement], str]:
        """Load requirements from local file."""
        content = self.file_reader.read(path)
        requirements = self.parser.parse(content)
        content_hash = self.compute_hash(content)
        return requirements, content_hash

    def fetch_upstream(self, url: str) -> tuple[list[Requirement], str]:
        """Fetch requirements from upstream URL."""
        content = self.url_fetcher.fetch(url)
        requirements = self.parser.parse(content)
        content_hash = self.compute_hash(content)
        return requirements, content_hash

    def compare(
        self,
        local: list[Requirement],
        upstream: list[Requirement],
    ) -> DriftResult:
        """Compare local and upstream requirements."""
        local_by_id = {r.req_id: r for r in local}
        upstream_by_id = {r.req_id: r for r in upstream}

        local_ids = set(local_by_id.keys())
        upstream_ids = set(upstream_by_id.keys())

        added_ids = upstream_ids - local_ids
        removed_ids = local_ids - upstream_ids
        common_ids = local_ids & upstream_ids

        result = DriftResult(
            local_count=len(local),
            upstream_count=len(upstream),
        )

        result.added = [upstream_by_id[rid] for rid in sorted(added_ids)]
        result.removed = [local_by_id[rid] for rid in sorted(removed_ids)]

        for rid in sorted(common_ids):
            local_req = local_by_id[rid]
            upstream_req = upstream_by_id[rid]
            if self._has_changes(local_req, upstream_req):
                result.modified.append((local_req, upstream_req))

        return result

    def _has_changes(self, local: Requirement, upstream: Requirement) -> bool:
        """Check if requirement has meaningful changes."""
        if local.description.strip() != upstream.description.strip():
            return True
        if local.level != upstream.level and upstream.level:
            return True
        return False

    def detect(
        self,
        local_path: Path,
        upstream_url: str | None = None,
        upstream_content: str | None = None,
    ) -> DriftResult:
        """
        Detect drift between local and upstream.

        Args:
            local_path: Path to local ASVS JSON file
            upstream_url: URL to fetch upstream (mutually exclusive with upstream_content)
            upstream_content: Direct upstream content (for testing)

        Returns:
            DriftResult with detected changes
        """
        local_reqs, local_hash = self.load_local(local_path)

        if upstream_content is not None:
            upstream_reqs = self.parser.parse(upstream_content)
            upstream_hash = self.compute_hash(upstream_content)
        elif upstream_url:
            upstream_reqs, upstream_hash = self.fetch_upstream(upstream_url)
        else:
            upstream_reqs, upstream_hash = self.fetch_upstream(UPSTREAM_ASVS_URL)

        result = self.compare(local_reqs, upstream_reqs)
        result.local_hash = local_hash
        result.upstream_hash = upstream_hash

        return result


# --- Output Formatters ---

class TextFormatter:
    """Format drift results as human-readable text."""

    def format(self, result: DriftResult) -> str:
        lines = [
            "=" * 60,
            "ASVS Drift Detection Report",
            "=" * 60,
            "",
            f"Local requirements:    {result.local_count} (hash: {result.local_hash})",
            f"Upstream requirements: {result.upstream_count} (hash: {result.upstream_hash})",
            "",
        ]

        if not result.has_drift:
            lines.append("Status: IN SYNC - No drift detected")
            lines.append("")
            return "\n".join(lines)

        lines.append(f"Status: DRIFT DETECTED - {result.summary}")
        lines.append("")

        if result.added:
            lines.append("-" * 40)
            lines.append(f"ADDED ({len(result.added)} requirements in upstream):")
            lines.append("-" * 40)
            for req in result.added:
                lines.append(f"  + {req.req_id}: {req.description[:80]}...")
            lines.append("")

        if result.removed:
            lines.append("-" * 40)
            lines.append(f"REMOVED ({len(result.removed)} requirements not in upstream):")
            lines.append("-" * 40)
            for req in result.removed:
                lines.append(f"  - {req.req_id}: {req.description[:80]}...")
            lines.append("")

        if result.modified:
            lines.append("-" * 40)
            lines.append(f"MODIFIED ({len(result.modified)} requirements changed):")
            lines.append("-" * 40)
            for local_req, upstream_req in result.modified:
                lines.append(f"  ~ {local_req.req_id}:")
                lines.append(f"    Local:    {local_req.description[:60]}...")
                lines.append(f"    Upstream: {upstream_req.description[:60]}...")
            lines.append("")

        return "\n".join(lines)


class JsonFormatter:
    """Format drift results as JSON."""

    def format(self, result: DriftResult) -> str:
        data = {
            "status": "drift" if result.has_drift else "in_sync",
            "summary": result.summary,
            "local": {
                "count": result.local_count,
                "hash": result.local_hash,
            },
            "upstream": {
                "count": result.upstream_count,
                "hash": result.upstream_hash,
            },
            "added": [
                {"id": r.req_id, "description": r.description}
                for r in result.added
            ],
            "removed": [
                {"id": r.req_id, "description": r.description}
                for r in result.removed
            ],
            "modified": [
                {
                    "id": local.req_id,
                    "local_description": local.description,
                    "upstream_description": upstream.description,
                }
                for local, upstream in result.modified
            ],
        }
        return json.dumps(data, indent=2)


# --- CLI Interface ---

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="drift-detector",
        description="Compare local ASVS implementation against upstream standard",
        epilog="Example: drift-detector --local 01-ASVS-Core-Reference/ASVS-5.0-en.json",
    )

    parser.add_argument(
        "--local",
        type=Path,
        help=f"Path to local ASVS JSON file (default: {DEFAULT_LOCAL_PATH})",
    )

    parser.add_argument(
        "--upstream-url",
        type=str,
        default=UPSTREAM_ASVS_URL,
        help="URL to fetch upstream ASVS (default: OWASP GitHub)",
    )

    parser.add_argument(
        "--upstream-file",
        type=Path,
        help="Path to upstream file (instead of fetching from URL)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path for finding local files (default: current directory)",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip upstream fetch (only validate local file parsing)",
    )

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    try:
        file_reader = DefaultFileReader()
        url_fetcher = DefaultUrlFetcher()
        req_parser = RequirementParser()
        detector = DriftDetector(file_reader, url_fetcher, req_parser)

        if parsed.local:
            local_path = parsed.local
        else:
            local_path = parsed.base_path / DEFAULT_LOCAL_PATH

        if not local_path.exists():
            print(f"Error: Local file not found: {local_path}", file=sys.stderr)
            return 1

        upstream_content = None
        upstream_url = None

        if parsed.offline:
            local_reqs, local_hash = detector.load_local(local_path)
            result = DriftResult(
                local_count=len(local_reqs),
                local_hash=local_hash,
                upstream_count=0,
                upstream_hash="(offline mode)",
            )
        elif parsed.upstream_file:
            upstream_content = file_reader.read(parsed.upstream_file)
            result = detector.detect(local_path, upstream_content=upstream_content)
        else:
            upstream_url = parsed.upstream_url
            result = detector.detect(local_path, upstream_url=upstream_url)

        if parsed.format == "json":
            formatter = JsonFormatter()
        else:
            formatter = TextFormatter()

        print(formatter.format(result))

        return 1 if result.has_drift else 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Hint: Use --offline to skip upstream fetch", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
