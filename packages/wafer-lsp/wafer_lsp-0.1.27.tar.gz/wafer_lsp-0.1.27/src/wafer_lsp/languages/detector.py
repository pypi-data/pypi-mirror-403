from pathlib import Path


class LanguageDetector:
    """Detects language based on file extension and content markers.
    
    Supports both extension-based detection (fast) and content-based detection
    (for files that share extensions, e.g., .cpp files that could be HIP or CUDA).
    """

    def __init__(self):
        self._extensions: dict[str, str] = {}
        self._content_markers: dict[str, list[str]] = {}  # language_id -> markers
        # Compound extensions like .hip.cpp need special handling
        self._compound_extensions: dict[str, str] = {}

    def register_extension(self, extension: str, language_id: str):
        normalized_ext = extension if extension.startswith(".") else f".{extension}"
        
        # Check if this is a compound extension (e.g., .hip.cpp)
        if normalized_ext.count(".") > 1:
            self._compound_extensions[normalized_ext] = language_id
        else:
            self._extensions[normalized_ext] = language_id

    def register_content_markers(self, language_id: str, markers: list[str]):
        """Register content markers for content-based language detection."""
        self._content_markers[language_id] = markers

    def detect_from_uri(self, uri: str, content: str | None = None) -> str | None:
        """Detect language from URI and optionally content.
        
        Args:
            uri: File URI or path
            content: Optional file content for content-based detection
            
        Returns:
            Language ID or None
        """
        if uri.startswith("file://"):
            file_path = uri[7:]
        else:
            file_path = uri

        return self.detect_from_path(file_path, content)

    def detect_from_path(self, file_path: str, content: str | None = None) -> str | None:
        """Detect language from file path and optionally content.
        
        Order of detection:
        1. Compound extensions (e.g., .hip.cpp) - most specific
        2. Content markers (for shared extensions like .cpp)
        3. Simple extension
        """
        path = Path(file_path)
        
        # 1. Check compound extensions first
        # Get the last two suffixes for compound extension detection
        suffixes = path.suffixes
        if len(suffixes) >= 2:
            compound_ext = "".join(suffixes[-2:]).lower()
            if compound_ext in self._compound_extensions:
                return self._compound_extensions[compound_ext]
        
        # 2. If content is provided, check content markers
        if content:
            content_lang = self._detect_from_content(content)
            if content_lang:
                return content_lang
        
        # 3. Fall back to simple extension
        ext = path.suffix.lower()
        return self._extensions.get(ext)

    def _detect_from_content(self, content: str) -> str | None:
        """Detect language based on content markers.
        
        Returns the language with the most matching markers.
        """
        best_match: str | None = None
        best_count = 0
        
        for language_id, markers in self._content_markers.items():
            match_count = sum(1 for marker in markers if marker in content)
            if match_count > best_count:
                best_count = match_count
                best_match = language_id
        
        # Require at least one marker match
        return best_match if best_count > 0 else None

    def detect_from_extension(self, extension: str) -> str | None:
        normalized_ext = extension if extension.startswith(".") else f".{extension}"
        normalized_ext = normalized_ext.lower()  # Case insensitive
        return self._extensions.get(normalized_ext)

    def get_supported_extensions(self) -> list[str]:
        all_extensions = list(self._extensions.keys())
        all_extensions.extend(self._compound_extensions.keys())
        return all_extensions

    def is_supported(self, uri: str, content: str | None = None) -> bool:
        return self.detect_from_uri(uri, content) is not None

    def get_content_markers(self, language_id: str) -> list[str]:
        """Get content markers for a language."""
        return self._content_markers.get(language_id, [])
