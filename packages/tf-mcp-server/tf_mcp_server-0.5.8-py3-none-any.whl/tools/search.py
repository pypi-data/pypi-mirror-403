"""Full-text search tool for documentation."""

import re
from typing import Dict, List, Optional

from ..resources.docs_loader import DocsLoader
from ..resources.api_loader import ApiLoader


class SearchResult:
    """Represents a search result."""

    def __init__(
        self,
        uri: str,
        title: str,
        description: str,
        category: str,
        score: float,
        snippet: str,
        source_type: str,  # "doc" or "api"
    ):
        self.uri = uri
        self.title = title
        self.description = description
        self.category = category
        self.score = score
        self.snippet = snippet
        self.source_type = source_type

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "uri": self.uri,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "score": self.score,
            "snippet": self.snippet,
            "source_type": self.source_type,
        }


class SearchTool:
    """Full-text search across documentation and API specs."""

    def __init__(self, docs_loader: DocsLoader, api_loader: ApiLoader):
        self.docs_loader = docs_loader
        self.api_loader = api_loader

    def search(
        self,
        query: str,
        limit: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search across all documentation.

        Args:
            query: The search query string
            limit: Maximum number of results to return
            source_filter: Filter by source type ("docs", "api", or None for all)

        Returns:
            List of search results with scores
        """
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        # Search markdown docs
        if source_filter is None or source_filter == "docs":
            for doc in self.docs_loader.get_all_docs():
                score = self._calculate_score(query_terms, doc.title, doc.content)
                if score > 0:
                    snippet = self._extract_snippet(doc.content, query_terms)
                    results.append(SearchResult(
                        uri=doc.uri,
                        title=doc.title,
                        description=doc.description,
                        category=doc.category,
                        score=score,
                        snippet=snippet,
                        source_type="doc",
                    ))

        # Search API specs
        if source_filter is None or source_filter == "api":
            for spec in self.api_loader.get_all_specs():
                # Search in spec title and description
                spec_text = f"{spec.title} {spec.description}"
                score = self._calculate_score(query_terms, spec.title, spec_text)

                # Also search in endpoints
                for endpoint in spec.get_endpoints_summary():
                    endpoint_text = f"{endpoint['path']} {endpoint['summary']} {endpoint['description']}"
                    endpoint_score = self._calculate_score(
                        query_terms,
                        endpoint['summary'] or endpoint['path'],
                        endpoint_text
                    )
                    if endpoint_score > score:
                        score = endpoint_score

                if score > 0:
                    snippet = self._generate_api_snippet(spec, query_terms)
                    results.append(SearchResult(
                        uri=spec.uri,
                        title=spec.title,
                        description=spec.description,
                        category="api",
                        score=score,
                        snippet=snippet,
                        source_type="api",
                    ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        # Limit results
        results = results[:limit]

        return [r.to_dict() for r in results]

    def _calculate_score(
        self,
        query_terms: List[str],
        title: str,
        content: str,
    ) -> float:
        """Calculate relevance score for a document."""
        score = 0.0
        title_lower = title.lower()
        content_lower = content.lower()

        for term in query_terms:
            # Title match is worth more
            if term in title_lower:
                score += 10.0
                # Exact title match bonus
                if title_lower == term:
                    score += 5.0

            # Content matches
            content_count = content_lower.count(term)
            if content_count > 0:
                # Diminishing returns for many matches
                score += min(content_count, 10) * 1.0

        return score

    def _extract_snippet(
        self,
        content: str,
        query_terms: List[str],
        max_length: int = 200,
    ) -> str:
        """Extract a relevant snippet from content."""
        content_lower = content.lower()

        # Find the first occurrence of any query term
        best_pos = len(content)
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1 and pos < best_pos:
                best_pos = pos

        if best_pos == len(content):
            # No match found, return beginning of content
            best_pos = 0

        # Extract snippet around the match
        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + max_length - 50)

        snippet = content[start:end]

        # Clean up snippet
        snippet = " ".join(snippet.split())  # Normalize whitespace

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _generate_api_snippet(
        self,
        spec,
        query_terms: List[str],
    ) -> str:
        """Generate a snippet for an API spec."""
        # Find matching endpoints
        matching_endpoints = []
        for endpoint in spec.get_endpoints_summary():
            endpoint_text = f"{endpoint['path']} {endpoint['summary']}".lower()
            for term in query_terms:
                if term in endpoint_text:
                    matching_endpoints.append(endpoint)
                    break

        if matching_endpoints:
            # Show first few matching endpoints with API type info
            snippets = []
            for ep in matching_endpoints[:3]:
                api_type_display = {
                    "platform": "Platform API",
                    "ai-services": "AI Services API",
                    "voice": "Voice API"
                }.get(ep.get('api_type', 'unknown'), 'API')
                snippets.append(f"{api_type_display}: {ep['method']} {ep['path']}")
            return " | ".join(snippets)

        # Fall back to spec description with API type
        api_type_display = {
            "platform": "Platform API",
            "ai-services": "AI Services API",
            "voice": "Voice API"
        }.get(spec.api_type, 'API')
        
        if spec.description:
            return f"{api_type_display}: {spec.description[:200]}"
        else:
            return f"{api_type_display}: {spec.title}"

    def search_endpoints(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search specifically for API endpoints.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of matching endpoints
        """
        return self.api_loader.search_endpoints(query)[:limit]

    def list_categories(self) -> List[str]:
        """List all available documentation categories."""
        return self.docs_loader.get_categories()

    def list_api_specs(self) -> List[Dict]:
        """List all available API specifications."""
        return self.api_loader.list_specs()
