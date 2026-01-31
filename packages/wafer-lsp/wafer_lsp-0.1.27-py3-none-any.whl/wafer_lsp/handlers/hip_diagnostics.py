"""
HIP Diagnostics Provider.

Generates warnings for common wavefront-related mistakes in HIP code.
AMD GPUs use 64-thread wavefronts (CDNA) vs CUDA's 32-thread warps,
and code written for CUDA often has hard-coded assumptions that break on AMD.

Diagnostic Codes:
- HIP001: Incorrect wavefront size assumption (using 32 instead of 64)
- HIP002: Wavefront intrinsic misuse
- HIP003: Ballot result handling errors (32-bit vs 64-bit)
- HIP004: Lane/wavefront index calculation errors
"""

from dataclasses import dataclass
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticTag,
    Position,
    Range,
)

from ..parsers.hip_parser import HIPParser, WavefrontPattern


@dataclass(frozen=True)
class HIPDiagnosticInfo:
    """Information about a HIP diagnostic."""
    code: str
    message: str
    severity: DiagnosticSeverity
    suggestion: str
    doc_link: str | None = None


# Diagnostic code to info mapping
DIAGNOSTIC_INFO: dict[str, HIPDiagnosticInfo] = {
    "HIP001": HIPDiagnosticInfo(
        code="HIP001",
        message="Potential wavefront size mismatch: AMD GPUs use 64-thread wavefronts, not 32.",
        severity=DiagnosticSeverity.Warning,
        suggestion="Use `warpSize` variable or `__AMDGCN_WAVEFRONT_SIZE__` macro instead of hard-coding 32.",
        doc_link="https://rocm.docs.amd.com/en/latest/",
    ),
    "HIP002": HIPDiagnosticInfo(
        code="HIP002",
        message="Wavefront intrinsic may behave differently on AMD GPUs.",
        severity=DiagnosticSeverity.Warning,
        suggestion="AMD wavefronts have 64 threads. Shuffle/ballot operations operate on the full wavefront. Adjust your code accordingly.",
    ),
    "HIP003": HIPDiagnosticInfo(
        code="HIP003",
        message="Ballot result comparison uses 32-bit mask, but AMD's __ballot returns 64-bit.",
        severity=DiagnosticSeverity.Warning,
        suggestion="Use `0xFFFFFFFFFFFFFFFFull` for 64-bit comparison. Use `__popcll()` to count bits.",
    ),
    "HIP004": HIPDiagnosticInfo(
        code="HIP004",
        message="Lane/wavefront index calculation assumes 32-thread warps.",
        severity=DiagnosticSeverity.Warning,
        suggestion="Use `warpSize` (64 on AMD CDNA) instead of hard-coding 32 for lane/warp calculations.",
    ),
}


# Map pattern types to diagnostic codes
PATTERN_TO_DIAGNOSTIC: dict[str, str] = {
    "warp_size_32": "HIP001",
    "shuffle_mask": "HIP002",
    "ballot_32bit": "HIP003",
    "lane_calc_32": "HIP004",
}


class HIPDiagnosticsProvider:
    """Provides diagnostics for HIP code.
    
    Detects patterns that indicate potential issues when running on AMD GPUs,
    particularly around wavefront size differences (64 vs 32).
    """

    def __init__(self):
        self._parser = HIPParser()

    def get_diagnostics(
        self,
        content: str,
        uri: str,
        enable_wavefront_diagnostics: bool = True,
    ) -> list[Diagnostic]:
        """Generate diagnostics for HIP code.
        
        Args:
            content: The document content
            uri: The document URI
            enable_wavefront_diagnostics: Whether to check for wavefront issues
            
        Returns:
            List of LSP Diagnostic objects
        """
        diagnostics: list[Diagnostic] = []
        
        if not enable_wavefront_diagnostics:
            return diagnostics

        # Parse the file to find wavefront patterns
        parsed = self._parser.parse_file(content)
        wavefront_patterns = parsed.get("wavefront_patterns", [])
        
        lines = content.split("\n")
        
        for pattern in wavefront_patterns:
            diagnostic = self._create_diagnostic_from_pattern(pattern, lines)
            if diagnostic:
                diagnostics.append(diagnostic)
        
        # Additional checks that require more context
        diagnostics.extend(self._check_warp_reduction_patterns(content, lines))
        diagnostics.extend(self._check_shuffle_width_parameters(content, lines))
        
        return diagnostics

    def _create_diagnostic_from_pattern(
        self,
        pattern: WavefrontPattern,
        lines: list[str],
    ) -> Diagnostic | None:
        """Create a diagnostic from a detected wavefront pattern."""
        diag_code = PATTERN_TO_DIAGNOSTIC.get(pattern.pattern_type)
        if not diag_code:
            return None

        diag_info = DIAGNOSTIC_INFO.get(diag_code)
        if not diag_info:
            return None

        # Find the problematic value in the line to highlight it
        line = lines[pattern.line] if pattern.line < len(lines) else ""
        start_char = line.find(pattern.problematic_value)
        if start_char == -1:
            start_char = 0
        end_char = start_char + len(pattern.problematic_value)

        range_ = Range(
            start=Position(line=pattern.line, character=start_char),
            end=Position(line=pattern.line, character=end_char),
        )

        message = self._format_diagnostic_message(
            diag_info,
            pattern.problematic_value,
            pattern.code_snippet,
        )

        return Diagnostic(
            range=range_,
            severity=diag_info.severity,
            code=diag_info.code,
            source="wafer-hip",
            message=message,
            data={"suggestion": diag_info.suggestion},
        )

    def _format_diagnostic_message(
        self,
        diag_info: HIPDiagnosticInfo,
        problematic_value: str,
        code_snippet: str,
    ) -> str:
        """Format the diagnostic message with context."""
        msg = diag_info.message
        
        # Add specific guidance based on the problematic value
        if problematic_value == "32":
            msg += f"\n\nFound: `{problematic_value}` (assumes CUDA warp size)"
            msg += "\nExpected: `warpSize` or `64` for AMD CDNA GPUs"
        elif problematic_value == "31":
            msg += f"\n\nFound: `& {problematic_value}` (assumes 32-thread warp)"
            msg += "\nExpected: `& (warpSize - 1)` or `& 63` for AMD CDNA GPUs"
        elif problematic_value == "0xFFFFFFFF":
            msg += f"\n\nFound: `{problematic_value}` (32-bit mask)"
            msg += "\nExpected: `0xFFFFFFFFFFFFFFFFull` (64-bit mask for AMD)"
        
        msg += f"\n\n💡 {diag_info.suggestion}"
        
        return msg

    def _check_warp_reduction_patterns(
        self,
        content: str,
        lines: list[str],
    ) -> list[Diagnostic]:
        """Check for warp reduction patterns that start from 16 instead of 32."""
        diagnostics: list[Diagnostic] = []
        
        # Look for reduction loops that start from 16 (half of CUDA warp)
        # This is a common CUDA pattern: for (int i = 16; i > 0; i >>= 1)
        import re
        
        pattern = re.compile(
            r'for\s*\(\s*(?:int|unsigned)\s+\w+\s*=\s*16\s*;[^;]*;\s*\w+\s*>>=\s*1\s*\)'
        )
        
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                diag_info = DIAGNOSTIC_INFO["HIP001"]
                
                range_ = Range(
                    start=Position(line=i, character=match.start()),
                    end=Position(line=i, character=match.end()),
                )
                
                diagnostics.append(Diagnostic(
                    range=range_,
                    severity=DiagnosticSeverity.Warning,
                    code="HIP001",
                    source="wafer-hip",
                    message=(
                        "Warp reduction loop starts from 16 (half CUDA warp).\n\n"
                        "For AMD's 64-thread wavefronts, start from 32:\n"
                        "`for (int offset = 32; offset > 0; offset >>= 1)`\n\n"
                        "Or better, use `warpSize / 2` for portability."
                    ),
                ))
        
        return diagnostics

    def _check_shuffle_width_parameters(
        self,
        content: str,
        lines: list[str],
    ) -> list[Diagnostic]:
        """Check for shuffle operations with explicit width=32."""
        diagnostics: list[Diagnostic] = []
        
        import re
        
        # Pattern for __shfl variants with explicit width parameter of 32
        # __shfl_down(val, offset, 32)
        patterns = [
            (re.compile(r'__shfl_down\s*\([^)]*,\s*(\d+)\s*,\s*32\s*\)'), "__shfl_down"),
            (re.compile(r'__shfl_up\s*\([^)]*,\s*(\d+)\s*,\s*32\s*\)'), "__shfl_up"),
            (re.compile(r'__shfl_xor\s*\([^)]*,\s*(\d+)\s*,\s*32\s*\)'), "__shfl_xor"),
            (re.compile(r'__shfl\s*\([^)]*,\s*(\d+)\s*,\s*32\s*\)'), "__shfl"),
        ]
        
        for i, line in enumerate(lines):
            for pattern, intrinsic_name in patterns:
                match = pattern.search(line)
                if match:
                    # Find position of "32" in the match
                    match_text = match.group(0)
                    pos_32 = match_text.rfind("32")
                    start_char = match.start() + pos_32
                    
                    range_ = Range(
                        start=Position(line=i, character=start_char),
                        end=Position(line=i, character=start_char + 2),
                    )
                    
                    diagnostics.append(Diagnostic(
                        range=range_,
                        severity=DiagnosticSeverity.Warning,
                        code="HIP002",
                        source="wafer-hip",
                        message=(
                            f"`{intrinsic_name}` with explicit width=32 assumes CUDA warp size.\n\n"
                            f"On AMD CDNA GPUs, wavefront size is 64. Either:\n"
                            f"• Remove the width parameter (defaults to `warpSize`)\n"
                            f"• Use `warpSize` as the width parameter\n\n"
                            f"Example: `{intrinsic_name}(val, offset)` or `{intrinsic_name}(val, offset, warpSize)`"
                        ),
                    ))
        
        return diagnostics


def create_hip_diagnostics_provider() -> HIPDiagnosticsProvider:
    """Create a HIP diagnostics provider instance."""
    return HIPDiagnosticsProvider()


def get_hip_diagnostics(
    content: str,
    uri: str,
    enable_wavefront_diagnostics: bool = True,
) -> list[Diagnostic]:
    """Convenience function to get HIP diagnostics for a file.
    
    Args:
        content: The document content
        uri: The document URI
        enable_wavefront_diagnostics: Whether to check for wavefront issues
        
    Returns:
        List of LSP Diagnostic objects
    """
    provider = create_hip_diagnostics_provider()
    return provider.get_diagnostics(content, uri, enable_wavefront_diagnostics)
