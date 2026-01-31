
from lsprotocol.types import Diagnostic

from ..languages.registry import get_language_registry
from .hip_diagnostics import get_hip_diagnostics


def handle_diagnostics(
    uri: str,
    content: str,
    enable_wavefront_diagnostics: bool = True,
) -> list[Diagnostic]:
    """Handle diagnostics for a document.
    
    Args:
        uri: Document URI
        content: Document content
        enable_wavefront_diagnostics: Whether to enable HIP wavefront warnings
        
    Returns:
        List of diagnostics
    """
    diagnostics: list[Diagnostic] = []

    registry = get_language_registry()
    language_info = registry.parse_file(uri, content)

    if not language_info:
        return diagnostics

    # Add HIP-specific diagnostics for HIP, CUDA, and C++ files
    # (C++ files might contain HIP code if they have HIP markers)
    if language_info.language in ("hip", "cuda", "cpp"):
        hip_diagnostics = get_hip_diagnostics(
            content,
            uri,
            enable_wavefront_diagnostics=enable_wavefront_diagnostics,
        )
        diagnostics.extend(hip_diagnostics)

    return diagnostics
