"""Loader for markdown documentation files."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter


class DocEntry:
    """Represents a loaded documentation entry."""

    def __init__(
        self,
        path: Path,
        category: str,
        slug: str,
        title: str,
        description: str,
        content: str,
        raw_content: str,
    ):
        self.path = path
        self.category = category
        self.slug = slug
        self.title = title
        self.description = description
        self.content = content  # Content without frontmatter
        self.raw_content = raw_content  # Original file content

    @property
    def uri(self) -> str:
        """Get the MCP resource URI for this doc."""
        return f"toothfairy://docs/{self.category}/{self.slug}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for search results."""
        return {
            "uri": self.uri,
            "category": self.category,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "path": str(self.path),
        }


class DocsLoader:
    """Loads and indexes markdown documentation files."""

    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self._docs: Dict[str, DocEntry] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all documentation files from the docs path."""
        if not self.docs_path.exists():
            raise FileNotFoundError(f"Documentation path not found: {self.docs_path}")

        self._docs.clear()

        # Find all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            # Skip files in node_modules or other non-doc directories
            if "node_modules" in str(md_file) or ".docusaurus" in str(md_file):
                continue

            try:
                doc = self._load_doc(md_file)
                if doc:
                    key = f"{doc.category}/{doc.slug}"
                    self._docs[key] = doc
            except Exception as e:
                print(f"Warning: Failed to load {md_file}: {e}")

        # Also load .mdx files
        for mdx_file in self.docs_path.rglob("*.mdx"):
            if "node_modules" in str(mdx_file) or ".docusaurus" in str(mdx_file):
                continue

            try:
                doc = self._load_doc(mdx_file)
                if doc:
                    key = f"{doc.category}/{doc.slug}"
                    self._docs[key] = doc
            except Exception as e:
                print(f"Warning: Failed to load {mdx_file}: {e}")

        self._loaded = True

    def _load_doc(self, file_path: Path) -> Optional[DocEntry]:
        """Load a single documentation file."""
        raw_content = file_path.read_text(encoding="utf-8")

        # Parse frontmatter
        try:
            post = frontmatter.loads(raw_content)
            content = post.content
            metadata = post.metadata
        except Exception:
            # If frontmatter parsing fails, use raw content
            content = raw_content
            metadata = {}

        # Determine category from directory structure
        rel_path = file_path.relative_to(self.docs_path)
        parts = rel_path.parts

        if len(parts) > 1:
            category = parts[0].lower()
        else:
            category = "general"

        # Generate slug from filename
        slug = self._generate_slug(file_path.stem)

        # Extract title from metadata or first heading
        title = metadata.get("title") or metadata.get("sidebar_label")
        if not title:
            title = self._extract_title(content) or self._title_from_slug(slug)

        # Extract description from metadata or first paragraph
        description = metadata.get("description", "")
        if not description:
            description = self._extract_description(content)

        return DocEntry(
            path=file_path,
            category=category,
            slug=slug,
            title=title,
            description=description,
            content=content,
            raw_content=raw_content,
        )

    def _generate_slug(self, filename: str) -> str:
        """Generate a URL-friendly slug from a filename."""
        # Remove numeric prefixes like "01-", "02-"
        slug = re.sub(r"^\d+[-_]", "", filename)
        # Convert to lowercase and replace spaces/underscores with hyphens
        slug = slug.lower().replace("_", "-").replace(" ", "-")
        # Remove any non-alphanumeric characters except hyphens
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    def _title_from_slug(self, slug: str) -> str:
        """Convert a slug to a title."""
        return slug.replace("-", " ").title()

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract the first H1 heading from markdown content."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_description(self, content: str, max_length: int = 200) -> str:
        """Extract a description from the first paragraph."""
        # Remove headings and get first paragraph
        lines = content.split("\n")
        paragraph_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip empty lines and headings
            if not stripped or stripped.startswith("#"):
                if paragraph_lines:
                    break
                continue
            # Skip code blocks and imports
            if stripped.startswith("```") or stripped.startswith("import"):
                if paragraph_lines:
                    break
                continue
            paragraph_lines.append(stripped)

        description = " ".join(paragraph_lines)
        if len(description) > max_length:
            description = description[:max_length].rsplit(" ", 1)[0] + "..."
        return description

    def get_doc(self, category: str, slug: str) -> Optional[DocEntry]:
        """Get a specific documentation entry."""
        if not self._loaded:
            self.load()
        return self._docs.get(f"{category}/{slug}")

    def get_all_docs(self) -> List[DocEntry]:
        """Get all loaded documentation entries."""
        if not self._loaded:
            self.load()
        return list(self._docs.values())

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        if not self._loaded:
            self.load()
        return sorted(set(doc.category for doc in self._docs.values()))

    def list_docs(self) -> List[Dict]:
        """List all documents with their metadata."""
        if not self._loaded:
            self.load()
        return [doc.to_dict() for doc in self._docs.values()]
