"""Loader for OpenAPI specification files."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ApiSpecEntry:
    """Represents a loaded OpenAPI specification."""

    def __init__(
        self,
        path: Path,
        name: str,
        title: str,
        description: str,
        version: str,
        content: Dict,
        raw_content: str,
    ):
        self.path = path
        self.name = name
        self.title = title
        self.description = description
        self.version = version
        self.content = content  # Parsed JSON
        self.raw_content = raw_content  # Original JSON string
        
        # Determine API type and base domain
        self.api_type = self._determine_api_type()
        self.base_domain = self._get_base_domain()
    
    def _determine_api_type(self) -> str:
        """Determine the type of API based on filename and content."""
        # The name already matches the API type due to KNOWN_SPECS mapping
        if self.name in ["platform", "ai-services", "voice", "voice-yaml"]:
            return self.name
        else:
            return "unknown"
    
    def _get_base_domain(self) -> str:
        """Get the base domain for this API type."""
        if self.api_type == "platform":
            return "api.{region}.toothfairyai.com"
        elif self.api_type == "ai-services":
            return "ai.{region}.toothfairyai.com"
        elif self.api_type == "voice":
            return "voice.{region}.toothfairyai.com"
        else:
            return "api.{region}.toothfairyai.com"

    @property
    def uri(self) -> str:
        """Get the MCP resource URI for this spec."""
        return f"toothfairy://api/{self.name}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for search results."""
        return {
            "uri": self.uri,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "path": str(self.path),
            "api_type": self.api_type,
            "base_domain": self.base_domain,
        }

    def get_endpoints_summary(self) -> List[Dict]:
        """Get a summary of all endpoints in the spec."""
        endpoints = []
        paths = self.content.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    # Get servers from OpenAPI spec
                    servers = self.content.get("servers", [])
                    base_url = "https://" + self.base_domain if servers else self.base_domain
                    
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "full_url": f"{base_url}{path}",
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "tags": details.get("tags", []),
                        "api_type": self.api_type,
                        "base_domain": self.base_domain,
                    })

        return endpoints


class ApiLoader:
    """Loads and indexes OpenAPI specification files."""

    # Known API spec files
    KNOWN_SPECS = {
        "openapi.json": "platform",
        "aiopenapi.json": "ai-services",
        "voiceapi.json": "voice",
        "voiceapi.yaml": "voice-yaml",
    }

    def __init__(self, api_docs_path: Path):
        self.api_docs_path = api_docs_path
        self._specs: Dict[str, ApiSpecEntry] = {}
        self._integration_guide: Optional[str] = None
        self._loaded = False

    def load(self) -> None:
        """Load all API specification files."""
        if not self.api_docs_path.exists():
            raise FileNotFoundError(f"API docs path not found: {self.api_docs_path}")

        self._specs.clear()

        # Load known OpenAPI JSON files
        for filename, name in self.KNOWN_SPECS.items():
            file_path = self.api_docs_path / filename
            if file_path.exists() and filename.endswith(".json"):
                try:
                    spec = self._load_spec(file_path, name)
                    if spec:
                        self._specs[name] = spec
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {e}")

        # Load integration guide if present
        guide_path = self.api_docs_path / "INTEGRATION_GUIDE.md"
        if guide_path.exists():
            try:
                self._integration_guide = guide_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Warning: Failed to load integration guide: {e}")

        self._loaded = True

    def _load_spec(self, file_path: Path, name: str) -> Optional[ApiSpecEntry]:
        """Load a single OpenAPI specification file."""
        raw_content = file_path.read_text(encoding="utf-8")

        try:
            content = json.loads(raw_content)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {file_path}: {e}")
            return None

        # Extract info from OpenAPI spec
        info = content.get("info", {})
        title = info.get("title", name.title())
        description = info.get("description", "")
        version = info.get("version", "unknown")

        return ApiSpecEntry(
            path=file_path,
            name=name,
            title=title,
            description=description,
            version=version,
            content=content,
            raw_content=raw_content,
        )

    def get_spec(self, name: str) -> Optional[ApiSpecEntry]:
        """Get a specific API specification."""
        if not self._loaded:
            self.load()
        return self._specs.get(name)

    def get_all_specs(self) -> List[ApiSpecEntry]:
        """Get all loaded API specifications."""
        if not self._loaded:
            self.load()
        return list(self._specs.values())

    def get_integration_guide(self) -> Optional[str]:
        """Get the integration guide content."""
        if not self._loaded:
            self.load()
        return self._integration_guide

    def list_specs(self) -> List[Dict]:
        """List all API specs with their metadata."""
        if not self._loaded:
            self.load()
        return [spec.to_dict() for spec in self._specs.values()]

    def get_all_endpoints(self) -> List[Dict]:
        """Get all endpoints across all specs."""
        if not self._loaded:
            self.load()

        all_endpoints = []
        for spec in self._specs.values():
            for endpoint in spec.get_endpoints_summary():
                endpoint["spec"] = spec.name
                all_endpoints.append(endpoint)

        return all_endpoints

    def search_endpoints(self, query: str) -> List[Dict]:
        """Search endpoints by path, summary, or description."""
        query_lower = query.lower()
        results = []

        for endpoint in self.get_all_endpoints():
            # Search in path, summary, description, and tags
            searchable = " ".join([
                endpoint.get("path", ""),
                endpoint.get("summary", ""),
                endpoint.get("description", ""),
                " ".join(endpoint.get("tags", [])),
            ]).lower()

            if query_lower in searchable:
                results.append(endpoint)

        return results
