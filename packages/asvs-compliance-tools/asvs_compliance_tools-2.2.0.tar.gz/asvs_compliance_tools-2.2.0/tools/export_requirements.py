#!/usr/bin/env python3
"""
ASVS Requirements Export Tool

Exports ASVS requirements to CSV or Jira-compatible JSON format.
Implements security controls including hash verification of source data.

ASVS Requirements Addressed:
- V1.5.2: Safe deserialization (JSON parsing with validation)
- V15.1.2: Maintain requirement inventory catalog
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


# --- Data Classes ---

@dataclass
class Requirement:
    """Represents a single ASVS requirement."""
    chapter_id: str
    chapter_name: str
    section_id: str
    section_name: str
    req_id: str
    req_description: str
    level: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Requirement":
        """Create a Requirement from a dictionary with validation."""
        required_fields = ["chapter_id", "chapter_name", "section_id", 
                          "section_name", "req_id", "req_description", "L"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            chapter_id=str(data["chapter_id"]),
            chapter_name=str(data["chapter_name"]),
            section_id=str(data["section_id"]),
            section_name=str(data["section_name"]),
            req_id=str(data["req_id"]),
            req_description=str(data["req_description"]),
            level=str(data["L"]),
        )


# --- Protocols for Dependency Injection ---

class FileReader(Protocol):
    """Protocol for reading file contents."""
    def read(self, path: Path) -> str: ...


class OutputWriter(Protocol):
    """Protocol for writing output."""
    def write(self, content: str) -> None: ...


# --- Concrete Implementations ---

class DefaultFileReader:
    """Default file reader implementation."""
    
    def read(self, path: Path) -> str:
        """Read file contents with UTF-8 encoding."""
        return path.read_text(encoding="utf-8")


class StdoutWriter:
    """Write to stdout."""
    
    def write(self, content: str) -> None:
        """Write content to stdout."""
        print(content, end="")


class FileWriter:
    """Write to a file."""
    
    def __init__(self, path: Path):
        self.path = path
    
    def write(self, content: str) -> None:
        """Write content to file."""
        self.path.write_text(content, encoding="utf-8")


# --- Hash Verification (Security Control) ---

class IntegrityVerifier:
    """Verifies integrity of source files using SHA-256 hashes."""
    
    def __init__(self, file_reader: FileReader):
        self.file_reader = file_reader
    
    def compute_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file contents."""
        content = self.file_reader.read(path)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def verify(self, path: Path, expected_hash: str | None = None) -> tuple[bool, str]:
        """
        Verify file integrity.
        
        Returns:
            Tuple of (is_valid, computed_hash)
            If expected_hash is None, always returns True with computed hash.
        """
        computed = self.compute_hash(path)
        if expected_hash is None:
            return True, computed
        return computed == expected_hash, computed


# --- Requirements Loading ---

class RequirementsLoader:
    """Loads and parses ASVS requirements from JSON files."""
    
    LEVEL_HIERARCHY = {"1": 1, "2": 2, "3": 3}
    
    def __init__(self, file_reader: FileReader, verifier: IntegrityVerifier):
        self.file_reader = file_reader
        self.verifier = verifier
    
    def load(self, path: Path, expected_hash: str | None = None) -> list[Requirement]:
        """
        Load requirements from JSON file with optional integrity verification.
        
        Args:
            path: Path to the JSON file
            expected_hash: Optional SHA-256 hash for verification
            
        Returns:
            List of Requirement objects
            
        Raises:
            ValueError: If hash verification fails or JSON is malformed
        """
        is_valid, computed_hash = self.verifier.verify(path, expected_hash)
        if not is_valid:
            raise ValueError(
                f"Integrity check failed for {path}. "
                f"Expected: {expected_hash}, Got: {computed_hash}"
            )
        
        content = self.file_reader.read(path)
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
        
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array in {path}, got {type(data).__name__}")
        
        requirements = []
        for idx, item in enumerate(data):
            try:
                requirements.append(Requirement.from_dict(item))
            except ValueError as e:
                raise ValueError(f"Invalid requirement at index {idx}: {e}")
        
        return requirements
    
    def filter_by_level(
        self, requirements: list[Requirement], level: str
    ) -> list[Requirement]:
        """
        Filter requirements by level.
        
        Level filtering is inclusive of lower levels:
        - L1: Only L1 requirements
        - L2: L1 and L2 requirements  
        - L3: L1, L2, and L3 requirements
        """
        if level not in self.LEVEL_HIERARCHY:
            raise ValueError(f"Invalid level: {level}. Must be one of: 1, 2, 3")
        
        max_level = self.LEVEL_HIERARCHY[level]
        return [
            req for req in requirements
            if self.LEVEL_HIERARCHY.get(req.level, 99) <= max_level
        ]


# --- Export Formatters ---

class Exporter(ABC):
    """Abstract base class for requirement exporters."""
    
    @abstractmethod
    def export(self, requirements: list[Requirement]) -> str:
        """Export requirements to string format."""
        pass


class CsvExporter(Exporter):
    """Export requirements to CSV format compatible with Jira/GitHub import."""
    
    HEADERS = [
        "Issue Key",
        "Summary", 
        "Description",
        "Labels",
        "Chapter",
        "Section",
    ]
    
    def export(self, requirements: list[Requirement]) -> str:
        """Export requirements to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        writer.writerow(self.HEADERS)
        
        for req in requirements:
            writer.writerow([
                req.req_id,
                f"[ASVS {req.req_id}] {req.section_name}",
                req.req_description,
                f"asvs,security,L{req.level},{req.chapter_id}",
                req.chapter_name,
                req.section_name,
            ])
        
        return output.getvalue()


class JiraJsonExporter(Exporter):
    """Export requirements to Jira-compatible JSON format."""
    
    def export(self, requirements: list[Requirement]) -> str:
        """Export requirements to Jira JSON string."""
        issues = []
        
        for req in requirements:
            issues.append({
                "summary": f"[ASVS {req.req_id}] {req.section_name}",
                "description": req.req_description,
                "labels": [
                    "asvs",
                    "security",
                    f"L{req.level}",
                    req.chapter_id.lower(),
                ],
                "customFields": {
                    "asvsId": req.req_id,
                    "asvsChapter": req.chapter_name,
                    "asvsSection": req.section_name,
                    "asvsLevel": req.level,
                },
            })
        
        return json.dumps({"issues": issues}, indent=2)


# --- CLI Interface ---

def get_exporter(format_type: str) -> Exporter:
    """Factory function to get the appropriate exporter."""
    exporters = {
        "csv": CsvExporter,
        "jira-json": JiraJsonExporter,
    }
    if format_type not in exporters:
        raise ValueError(f"Unknown format: {format_type}")
    return exporters[format_type]()


def find_source_file(level: str, base_path: Path) -> Path:
    """Find the appropriate source file for the given level."""
    core_ref = base_path / "01-ASVS-Core-Reference"
    
    level_files = {
        "1": core_ref / "ASVS-L1-Baseline.json",
        "2": core_ref / "ASVS-L2-Standard.json",
        "3": core_ref / "ASVS-5.0-en.json",
    }
    
    if level not in level_files:
        raise ValueError(f"Invalid level: {level}")
    
    path = level_files[level]
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    
    return path


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="export-requirements",
        description="Export ASVS requirements to CSV or Jira JSON format",
        epilog="Example: export-requirements --level 2 --format csv > requirements.csv",
    )
    
    parser.add_argument(
        "--level",
        choices=["1", "2", "3"],
        default="2",
        help="ASVS level to export (1=Baseline, 2=Standard, 3=Advanced). Default: 2",
    )
    
    parser.add_argument(
        "--format",
        choices=["csv", "jira-json"],
        default="csv",
        help="Output format. Default: csv",
    )
    
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to source JSON file (overrides --level for file selection)",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    
    parser.add_argument(
        "--verify-hash",
        metavar="HASH",
        help="Expected SHA-256 hash of source file for integrity verification",
    )
    
    parser.add_argument(
        "--show-hash",
        action="store_true",
        help="Print the SHA-256 hash of the source file and exit",
    )
    
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path for finding source files (default: current directory)",
    )
    
    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    try:
        file_reader = DefaultFileReader()
        verifier = IntegrityVerifier(file_reader)
        loader = RequirementsLoader(file_reader, verifier)
        
        if parsed.source:
            source_path = parsed.source
        else:
            source_path = find_source_file(parsed.level, parsed.base_path)
        
        if parsed.show_hash:
            hash_value = verifier.compute_hash(source_path)
            print(f"{hash_value}  {source_path}")
            return 0
        
        requirements = loader.load(source_path, parsed.verify_hash)
        
        if not parsed.source:
            requirements = loader.filter_by_level(requirements, parsed.level)
        
        exporter = get_exporter(parsed.format)
        output = exporter.export(requirements)
        
        if parsed.output:
            writer = FileWriter(parsed.output)
        else:
            writer = StdoutWriter()
        
        writer.write(output)
        
        return 0
        
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
