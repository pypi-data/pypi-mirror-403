"""Loader for release notes documentation."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter


class ReleaseNote:
    """Represents a loaded release note entry."""

    def __init__(
        self,
        path: Path,
        filename: str,
        version: str,
        release_date: str,
        title: str,
        summary: str,
        content: str,
        raw_content: str,
    ):
        self.path = path
        self.filename = filename
        self.version = version
        self.release_date = release_date
        self.title = title
        self.summary = summary
        self.content = content
        self.raw_content = raw_content

    @property
    def uri(self) -> str:
        """Get the MCP resource URI for this release note."""
        return f"toothfairy://release-notes/{self.version}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for search results."""
        return {
            "uri": self.uri,
            "version": self.version,
            "release_date": self.release_date,
            "title": self.title,
            "summary": self.summary,
            "path": str(self.path),
        }


class ReleaseNotesLoader:
    """Loads and indexes release notes files."""

    def __init__(self, release_notes_path: Path):
        self.release_notes_path = release_notes_path
        self._notes: Dict[str, ReleaseNote] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all release notes from the release-notes path."""
        if not self.release_notes_path.exists():
            # Release notes path doesn't exist - that's okay, just return empty
            self._loaded = True
            return

        self._notes.clear()

        # Find all markdown files
        for md_file in self.release_notes_path.glob("*.md"):
            # Skip index.md, latest.md, and CLAUDE.md
            if md_file.name in ("index.md", "latest.md", "CLAUDE.md"):
                continue

            try:
                note = self._load_note(md_file)
                if note:
                    self._notes[note.version] = note
            except Exception as e:
                print(f"Warning: Failed to load {md_file}: {e}")

        self._loaded = True

    def _load_note(self, file_path: Path) -> Optional[ReleaseNote]:
        """Load a single release note file."""
        raw_content = file_path.read_text(encoding="utf-8")

        # Parse frontmatter if present
        try:
            post = frontmatter.loads(raw_content)
            content = post.content
        except Exception:
            content = raw_content

        # Extract version from content (e.g., "# What's New in Version 0.668.0")
        version = self._extract_version(content)
        if not version:
            # Try to extract from filename (release-notes-2026-01-17-feature-170126.md)
            version = self._version_from_filename(file_path.stem)

        # Extract release date
        release_date = self._extract_release_date(content)

        # Extract title (first heading)
        title = self._extract_title(content)

        # Extract summary (intro paragraph after date)
        summary = self._extract_summary(content)

        return ReleaseNote(
            path=file_path,
            filename=file_path.stem,
            version=version,
            release_date=release_date,
            title=title,
            summary=summary,
            content=content,
            raw_content=raw_content,
        )

    def _extract_version(self, content: str) -> Optional[str]:
        """Extract version number from content."""
        # Look for "Version X.Y.Z" pattern
        match = re.search(r"Version\s+(\d+\.\d+(?:\.\d+)?)", content, re.IGNORECASE)
        if match:
            return match.group(1)

        # Look for "vX.Y.Z" at the end of the file
        match = re.search(r"\bv(\d+\.\d+(?:\.\d+)?)\s*$", content, re.MULTILINE)
        if match:
            return match.group(1)

        return None

    def _version_from_filename(self, filename: str) -> str:
        """Generate a version-like identifier from filename."""
        # release-notes-2026-01-17-feature-170126 -> 2026-01-17
        match = re.search(r"release-notes-(\d{4}-\d{2}-\d{2})", filename)
        if match:
            return match.group(1)
        return filename

    def _extract_release_date(self, content: str) -> str:
        """Extract release date from content."""
        # Look for "*Released on Month DD, YYYY*" or similar
        match = re.search(
            r"\*Released\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})\*", content
        )
        if match:
            return match.group(1)

        # Look for date in different format
        match = re.search(r"Released:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})", content)
        if match:
            return match.group(1)

        return "Unknown"

    def _extract_title(self, content: str) -> str:
        """Extract title from first heading."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Release Notes"

    def _extract_summary(self, content: str, max_length: int = 300) -> str:
        """Extract summary from introduction paragraph."""
        lines = content.split("\n")
        summary_lines = []
        found_date = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and headings at the start
            if not stripped or stripped.startswith("#"):
                if summary_lines:
                    break
                continue

            # Skip the release date line
            if stripped.startswith("*Released"):
                found_date = True
                continue

            # After finding date, collect the intro paragraph
            if found_date and stripped:
                # Stop at next heading or empty line after content
                if stripped.startswith("#") or stripped.startswith("##"):
                    break
                summary_lines.append(stripped)
                # Usually intro is just one paragraph
                if len(" ".join(summary_lines)) > 100:
                    break

        summary = " ".join(summary_lines)
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        return summary

    def get_note(self, version: str) -> Optional[ReleaseNote]:
        """Get a specific release note by version."""
        if not self._loaded:
            self.load()

        # Direct lookup
        if version in self._notes:
            return self._notes[version]

        # Try with/without 'v' prefix
        if version.startswith("v"):
            return self._notes.get(version[1:])
        else:
            return self._notes.get(f"v{version}")

    def get_latest(self) -> Optional[ReleaseNote]:
        """Get the latest release note."""
        if not self._loaded:
            self.load()

        if not self._notes:
            # Try to load latest.md directly
            latest_path = self.release_notes_path / "latest.md"
            if latest_path.exists():
                return self._load_note(latest_path)
            return None

        # Sort by version number (assuming semantic versioning)
        def version_key(v: str) -> tuple:
            parts = re.findall(r"\d+", v)
            return tuple(int(p) for p in parts) if parts else (0,)

        sorted_versions = sorted(self._notes.keys(), key=version_key, reverse=True)
        return self._notes[sorted_versions[0]] if sorted_versions else None

    def get_all_notes(self) -> List[ReleaseNote]:
        """Get all loaded release notes, sorted by version (newest first)."""
        if not self._loaded:
            self.load()

        def version_key(note: ReleaseNote) -> tuple:
            parts = re.findall(r"\d+", note.version)
            return tuple(int(p) for p in parts) if parts else (0,)

        return sorted(self._notes.values(), key=version_key, reverse=True)

    def list_notes(self) -> List[Dict]:
        """List all release notes with metadata."""
        if not self._loaded:
            self.load()
        return [note.to_dict() for note in self.get_all_notes()]

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search release notes by content."""
        if not self._loaded:
            self.load()

        query_lower = query.lower()
        results = []

        for note in self._notes.values():
            # Search in title, summary, and content
            score = 0
            if query_lower in note.title.lower():
                score += 10
            if query_lower in note.summary.lower():
                score += 5
            if query_lower in note.content.lower():
                score += 1

            if score > 0:
                result = note.to_dict()
                result["score"] = score
                # Find a relevant snippet
                result["snippet"] = self._find_snippet(note.content, query)
                results.append(result)

        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _find_snippet(self, content: str, query: str, context: int = 100) -> str:
        """Find a snippet of content containing the query."""
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # Return first part of content as fallback
            return content[:200] + "..." if len(content) > 200 else content

        start = max(0, pos - context)
        end = min(len(content), pos + len(query) + context)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
