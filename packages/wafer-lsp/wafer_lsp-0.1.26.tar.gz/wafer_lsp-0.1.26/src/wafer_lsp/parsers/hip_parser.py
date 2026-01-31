"""
HIP Parser for wafer-lsp.

Extracts GPU constructs from HIP (AMD GPU) source files:
- __global__ kernels
- __device__ helper functions  
- __shared__ memory allocations (LDS)
- Kernel launch sites (<<<>>> and hipLaunchKernelGGL)
- Wavefront-sensitive patterns for diagnostics
"""

import re
from dataclasses import dataclass, field
from typing import Any

from .base_parser import BaseParser


@dataclass(frozen=True)
class HIPParameter:
    """A kernel or device function parameter."""
    name: str
    type_str: str
    is_pointer: bool = False
    is_const: bool = False


@dataclass(frozen=True)
class HIPKernel:
    """A __global__ GPU kernel function."""
    name: str
    line: int
    end_line: int
    parameters: list[str]
    parameter_info: list[HIPParameter]
    attributes: list[str]  # e.g., __launch_bounds__(256)
    docstring: str | None = None


@dataclass(frozen=True)
class HIPDeviceFunction:
    """A __device__ helper function."""
    name: str
    line: int
    end_line: int
    parameters: list[str]
    parameter_info: list[HIPParameter]
    return_type: str = "void"
    is_inline: bool = False


@dataclass(frozen=True)
class SharedMemoryAllocation:
    """A __shared__ memory (LDS) allocation."""
    name: str
    type_str: str
    line: int
    size_bytes: int | None  # None if dynamic/unknown
    array_size: str | None  # Array dimension if static
    is_dynamic: bool = False


@dataclass(frozen=True)
class KernelLaunchSite:
    """Where a kernel is launched."""
    kernel_name: str
    line: int
    grid_dim: str | None  # Grid dimensions if determinable
    block_dim: str | None  # Block dimensions if determinable
    shared_mem_bytes: str | None  # Dynamic shared memory size
    stream: str | None  # CUDA stream if specified
    is_hip_launch_kernel_ggl: bool = False  # True if using hipLaunchKernelGGL


@dataclass(frozen=True)
class WavefrontPattern:
    """A pattern that might indicate wavefront-size assumptions.
    
    These patterns often indicate code written for CUDA's 32-thread warps
    that may behave incorrectly on AMD's 64-thread wavefronts.
    """
    pattern_type: str  # "warp_size_32", "ballot_32bit", "shuffle_mask", "lane_calc_32"
    line: int
    code_snippet: str
    problematic_value: str  # The specific value causing concern (e.g., "32", "0xFFFFFFFF")
    severity: str = "warning"  # "warning", "error", "info"


class HIPParser(BaseParser):
    """Parser for HIP (AMD GPU) source files.
    
    Extracts kernels, device functions, shared memory allocations,
    launch sites, and wavefront-sensitive patterns using regex-based parsing.
    
    Why regex instead of full AST parsing:
    - HIP/CUDA syntax is C++ which is complex to fully parse
    - Key constructs (__global__, __device__, __shared__) are lexically distinct
    - Fast enough for real-time IDE use (<100ms)
    - Works on incomplete/invalid code during editing
    """

    # Regex patterns for HIP constructs
    
    # Matches __global__ function declarations
    # Captures: return type, function name
    # Note: __launch_bounds__ can be on the same line or line before
    _KERNEL_PATTERN = re.compile(
        r'(?:template\s*<[^>]*>\s*)?'  # Optional template
        r'(?:__launch_bounds__\s*\([^)]+\)\s*[\n\r]*)?'  # Optional launch bounds before __global__
        r'__global__\s+'
        r'(?:__device__\s+)?'  # Optional __device__ (CUDA allows both)
        r'(?:__launch_bounds__\s*\([^)]+\)\s*)?'  # Optional launch bounds after __global__
        r'([\w\s\*&:<>,]+?)\s+'  # Return type (usually void)
        r'(\w+)\s*'  # Function name (captured)
        r'\(',  # Start of parameter list
        re.MULTILINE | re.DOTALL
    )
    
    # Separate pattern to detect __launch_bounds__ near __global__
    _LAUNCH_BOUNDS_PATTERN = re.compile(
        r'__launch_bounds__\s*\(([^)]+)\)',
        re.MULTILINE
    )
    
    # Matches __device__ function declarations (not __global__)
    _DEVICE_FUNC_PATTERN = re.compile(
        r'(?:template\s*<[^>]*>\s*)?'  # Optional template
        r'__device__\s+'
        r'(?!__global__)'  # Not followed by __global__
        r'(__forceinline__\s+)?'  # Optional __forceinline__ (captured)
        r'(?:__host__\s+)?'  # Optional __host__
        r'(?:inline\s+)?'
        r'([\w\s\*&:<>,]+?)\s+'  # Return type (captured)
        r'(\w+)\s*'  # Function name (captured)
        r'\(',
        re.MULTILINE
    )
    
    # Matches __shared__ variable declarations (including 2D arrays)
    _SHARED_MEMORY_PATTERN = re.compile(
        r'__shared__\s+'
        r'([\w\s:<>,]+?)\s+'  # Type (captured)
        r'(\w+)\s*'  # Variable name (captured)
        r'(\[[^\]]*\](?:\s*\[[^\]]*\])?)?'  # Optional array size(s) including 2D (captured)
        r'\s*[;=]',
        re.MULTILINE
    )
    
    # Matches kernel launches with <<<>>> syntax
    _LAUNCH_SYNTAX_PATTERN = re.compile(
        r'(\w+)\s*'  # Kernel name (captured)
        r'<<<\s*'
        r'([^,>]+)\s*,\s*'  # Grid dim (captured)
        r'([^,>]+)'  # Block dim (captured)
        r'(?:\s*,\s*([^,>]+))?'  # Optional shared mem (captured)
        r'(?:\s*,\s*([^>]+))?'  # Optional stream (captured)
        r'\s*>>>',
        re.MULTILINE
    )
    
    # Matches hipLaunchKernelGGL calls
    _HIP_LAUNCH_PATTERN = re.compile(
        r'hipLaunchKernelGGL\s*\(\s*'
        r'(\w+)\s*,\s*'  # Kernel name (captured)
        r'([^,]+)\s*,\s*'  # Grid dim (captured)
        r'([^,]+)\s*,\s*'  # Block dim (captured)
        r'([^,]+)\s*,\s*'  # Shared mem (captured)
        r'([^,)]+)'  # Stream (captured)
        r'(?:\s*,)?',  # Optional comma before args
        re.MULTILINE
    )
    
    # Patterns that suggest incorrect wavefront size assumptions (CUDA's 32 vs AMD's 64)
    _WARP_SIZE_32_PATTERNS = [
        # threadIdx.x < 32, threadIdx.x % 32, threadIdx.x & 31
        (re.compile(r'threadIdx\s*\.\s*[xyz]\s*[<%&]\s*32\b'), "warp_size_32", "32"),
        (re.compile(r'threadIdx\s*\.\s*[xyz]\s*&\s*31\b'), "warp_size_32", "31"),
        (re.compile(r'threadIdx\s*\.\s*[xyz]\s*/\s*32\b'), "warp_size_32", "32"),
        
        # Lane/warp index calculations with hard-coded 32
        (re.compile(r'\blaneId\s*=\s*[^;]*%\s*32\b'), "lane_calc_32", "32"),
        (re.compile(r'\bwarpId\s*=\s*[^;]*/\s*32\b'), "lane_calc_32", "32"),
        (re.compile(r'\blane\s*=\s*[^;]*&\s*31\b'), "lane_calc_32", "31"),
        
        # Ballot result compared to 32-bit mask
        (re.compile(r'__ballot\s*\([^)]*\)\s*==\s*0x[Ff]{8}\b'), "ballot_32bit", "0xFFFFFFFF"),
        (re.compile(r'__ballot\s*\([^)]*\)\s*!=\s*0x[Ff]{8}\b'), "ballot_32bit", "0xFFFFFFFF"),
        (re.compile(r'__ballot\s*\([^)]*\)\s*&\s*0x[Ff]{8}\b'), "ballot_32bit", "0xFFFFFFFF"),
        
        # Shuffle operations with mask suggesting 32-thread warp
        (re.compile(r'__shfl(?:_sync)?\s*\([^)]*,\s*0x[Ff]{8}\s*\)'), "shuffle_mask", "0xFFFFFFFF"),
        # Match __shfl_down(val, offset, 32) or similar with explicit width=32
        (re.compile(r'__shfl_down(?:_sync)?\s*\([^,]+,\s*[^,]+,\s*32\s*\)'), "shuffle_mask", "32"),
        (re.compile(r'__shfl_up(?:_sync)?\s*\([^,]+,\s*[^,]+,\s*32\s*\)'), "shuffle_mask", "32"),
        (re.compile(r'__shfl_xor(?:_sync)?\s*\([^,]+,\s*[^,]+,\s*32\s*\)'), "shuffle_mask", "32"),
        (re.compile(r'__shfl(?:_sync)?\s*\([^,]+,\s*[^,]+,\s*32\s*\)'), "shuffle_mask", "32"),
        
        # activemask() compared to 32-bit value
        (re.compile(r'__activemask\s*\(\s*\)\s*==\s*0x[Ff]{8}\b'), "ballot_32bit", "0xFFFFFFFF"),
        
        # Hard-coded warp size
        (re.compile(r'#define\s+WARP_SIZE\s+32\b'), "warp_size_32", "32"),
        (re.compile(r'const(?:expr)?\s+\w+\s+(?:warp|WARP)_?(?:size|SIZE)\s*=\s*32\b'), "warp_size_32", "32"),
    ]

    def parse_file(self, content: str) -> dict[str, Any]:
        """Parse a HIP source file and extract GPU constructs.
        
        Args:
            content: The source file content as a string.
            
        Returns:
            Dictionary containing:
            - kernels: List of HIPKernel
            - device_functions: List of HIPDeviceFunction
            - shared_memory: List of SharedMemoryAllocation
            - launch_sites: List of KernelLaunchSite
            - wavefront_patterns: List of WavefrontPattern
        """
        kernels = self._extract_kernels(content)
        device_functions = self._extract_device_functions(content)
        shared_memory = self._extract_shared_memory(content)
        launch_sites = self._extract_launch_sites(content)
        wavefront_patterns = self._extract_wavefront_patterns(content)
        
        return {
            "kernels": kernels,
            "device_functions": device_functions,
            "shared_memory": shared_memory,
            "launch_sites": launch_sites,
            "wavefront_patterns": wavefront_patterns,
        }

    def _extract_kernels(self, content: str) -> list[HIPKernel]:
        """Extract all __global__ kernel functions."""
        kernels: list[HIPKernel] = []
        
        for match in self._KERNEL_PATTERN.finditer(content):
            line = content[:match.start()].count('\n')
            
            attributes = []
            
            # Look for __launch_bounds__ in the matched region or nearby
            # Search from a bit before the match to where __global__ ends
            search_start = max(0, match.start() - 50)
            search_end = match.end()
            search_region = content[search_start:search_end]
            
            lb_match = self._LAUNCH_BOUNDS_PATTERN.search(search_region)
            if lb_match:
                attributes.append(f"__launch_bounds__({lb_match.group(1)})")
            
            kernel_name = match.group(2)
            
            # Extract parameters
            params, param_info = self._extract_parameters(content, match.end() - 1)
            
            # Find end of function (approximate by finding matching brace)
            end_line = self._find_function_end(content, match.end())
            
            # Extract docstring (comment immediately before the kernel)
            docstring = self._extract_docstring(content, match.start())
            
            kernels.append(HIPKernel(
                name=kernel_name,
                line=line,
                end_line=end_line,
                parameters=params,
                parameter_info=param_info,
                attributes=attributes,
                docstring=docstring,
            ))
        
        return kernels

    def _extract_device_functions(self, content: str) -> list[HIPDeviceFunction]:
        """Extract all __device__ helper functions."""
        device_funcs: list[HIPDeviceFunction] = []
        
        for match in self._DEVICE_FUNC_PATTERN.finditer(content):
            # Skip if this is part of a __global__ __device__ combination
            prefix = content[max(0, match.start() - 50):match.start()]
            if '__global__' in prefix:
                continue
            
            line = content[:match.start()].count('\n')
            
            # Group 1 is __forceinline__ (optional), group 2 is return type, group 3 is func name
            forceinline_match = match.group(1)
            return_type = match.group(2).strip()
            func_name = match.group(3)
            
            # Check if inline (either captured in pattern or in prefix)
            is_inline = bool(forceinline_match) or \
                        '__forceinline__' in content[max(0, match.start() - 30):match.start()] or \
                        'inline' in content[max(0, match.start() - 20):match.start()]
            
            # Extract parameters
            params, param_info = self._extract_parameters(content, match.end() - 1)
            
            end_line = self._find_function_end(content, match.end())
            
            device_funcs.append(HIPDeviceFunction(
                name=func_name,
                line=line,
                end_line=end_line,
                parameters=params,
                parameter_info=param_info,
                return_type=return_type,
                is_inline=is_inline,
            ))
        
        return device_funcs

    def _extract_shared_memory(self, content: str) -> list[SharedMemoryAllocation]:
        """Extract all __shared__ memory declarations."""
        shared_mem: list[SharedMemoryAllocation] = []
        
        for match in self._SHARED_MEMORY_PATTERN.finditer(content):
            line = content[:match.start()].count('\n')
            
            type_str = match.group(1).strip()
            var_name = match.group(2)
            array_dims = match.group(3)  # Could be [n] or [n][m] for 2D
            
            # Clean up the array dimension string
            array_size = None
            if array_dims:
                # Remove brackets and combine dimensions
                array_size = array_dims.strip()
            
            # Try to compute size in bytes
            size_bytes = self._estimate_shared_mem_size(type_str, array_size)
            
            # Check if it's dynamic (extern __shared__)
            is_dynamic = 'extern' in content[max(0, match.start() - 20):match.start()]
            
            shared_mem.append(SharedMemoryAllocation(
                name=var_name,
                type_str=type_str,
                line=line,
                size_bytes=size_bytes,
                array_size=array_size,
                is_dynamic=is_dynamic,
            ))
        
        return shared_mem

    def _extract_launch_sites(self, content: str) -> list[KernelLaunchSite]:
        """Extract all kernel launch sites."""
        launch_sites: list[KernelLaunchSite] = []
        
        # <<<>>> syntax
        for match in self._LAUNCH_SYNTAX_PATTERN.finditer(content):
            line = content[:match.start()].count('\n')
            
            launch_sites.append(KernelLaunchSite(
                kernel_name=match.group(1),
                line=line,
                grid_dim=match.group(2).strip() if match.group(2) else None,
                block_dim=match.group(3).strip() if match.group(3) else None,
                shared_mem_bytes=match.group(4).strip() if match.group(4) else None,
                stream=match.group(5).strip() if match.group(5) else None,
                is_hip_launch_kernel_ggl=False,
            ))
        
        # hipLaunchKernelGGL
        for match in self._HIP_LAUNCH_PATTERN.finditer(content):
            line = content[:match.start()].count('\n')
            
            launch_sites.append(KernelLaunchSite(
                kernel_name=match.group(1),
                line=line,
                grid_dim=match.group(2).strip() if match.group(2) else None,
                block_dim=match.group(3).strip() if match.group(3) else None,
                shared_mem_bytes=match.group(4).strip() if match.group(4) else None,
                stream=match.group(5).strip() if match.group(5) else None,
                is_hip_launch_kernel_ggl=True,
            ))
        
        return launch_sites

    def _extract_wavefront_patterns(self, content: str) -> list[WavefrontPattern]:
        """Extract patterns that might indicate incorrect wavefront size assumptions.
        
        AMD GPUs use 64-thread wavefronts (CDNA) or configurable 32/64 (RDNA),
        while CUDA uses 32-thread warps. Code written for CUDA may have
        hard-coded assumptions about warp size that break on AMD.
        """
        patterns: list[WavefrontPattern] = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # Skip lines that use warpSize (correct portable code)
            if 'warpSize' in line or '__AMDGCN_WAVEFRONT_SIZE__' in line:
                continue
            
            for pattern_re, pattern_type, problematic_value in self._WARP_SIZE_32_PATTERNS:
                match = pattern_re.search(line)
                if match:
                    patterns.append(WavefrontPattern(
                        pattern_type=pattern_type,
                        line=i,
                        code_snippet=line.strip(),
                        problematic_value=problematic_value,
                    ))
        
        return patterns

    def _extract_parameters(self, content: str, paren_start: int) -> tuple[list[str], list[HIPParameter]]:
        """Extract function parameters starting from the opening parenthesis.
        
        Returns:
            Tuple of (parameter names list, detailed parameter info list)
        """
        if paren_start >= len(content) or content[paren_start] != '(':
            return [], []
        
        # Find matching closing paren
        depth = 0
        param_end = paren_start
        
        for i in range(paren_start, len(content)):
            char = content[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    param_end = i
                    break
        
        if param_end == paren_start:
            return [], []
        
        param_str = content[paren_start + 1:param_end]
        
        # Parse parameters handling templates and nested parens
        params: list[str] = []
        param_info: list[HIPParameter] = []
        current_param = ""
        template_depth = 0
        paren_depth = 0
        
        for char in param_str:
            if char == '<':
                template_depth += 1
                current_param += char
            elif char == '>':
                template_depth -= 1
                current_param += char
            elif char == '(':
                paren_depth += 1
                current_param += char
            elif char == ')':
                paren_depth -= 1
                current_param += char
            elif char == ',' and template_depth == 0 and paren_depth == 0:
                param = self._parse_single_parameter(current_param.strip())
                if param:
                    params.append(param.name)
                    param_info.append(param)
                current_param = ""
            else:
                current_param += char
        
        # Handle last parameter
        if current_param.strip():
            param = self._parse_single_parameter(current_param.strip())
            if param:
                params.append(param.name)
                param_info.append(param)
        
        return params, param_info

    def _parse_single_parameter(self, param_str: str) -> HIPParameter | None:
        """Parse a single parameter string into HIPParameter.
        
        Returns None if param_str cannot be parsed into a valid parameter.
        """
        if not param_str:
            return None
        
        # Remove default value if present
        if '=' in param_str:
            param_str = param_str.split('=')[0].strip()
        
        is_const = 'const' in param_str
        is_pointer = '*' in param_str or '&' in param_str
        
        # Extract name (last token after removing type qualifiers)
        parts = param_str.replace('*', ' * ').replace('&', ' & ').split()
        
        if not parts:
            return None
        
        # Find the parameter name (last identifier)
        name = parts[-1].strip('*&')
        
        # If we only have one part, we can't distinguish type from name
        # This could be a parameter like `void` (no name) or incomplete code
        if len(parts) == 1:
            # Assume it's just a name with unknown type
            type_str = ""
        else:
            # Reconstruct type from all parts except the last (name)
            type_parts = parts[:-1]
            type_str = ' '.join(type_parts).replace(' * ', '*').replace(' & ', '&')
        
        return HIPParameter(
            name=name,
            type_str=type_str,
            is_pointer=is_pointer,
            is_const=is_const,
        )

    def _find_function_end(self, content: str, start_pos: int) -> int:
        """Find the line number where a function ends (closing brace).
        
        Returns:
            Line number of closing brace, or start line if function body not found.
            
        Note: Returns start line (not an approximation) when closing brace cannot be found.
        This happens for incomplete code during editing - the caller should handle this case.
        """
        start_line = content[:start_pos].count('\n')
        
        # Find opening brace
        brace_pos = content.find('{', start_pos)
        if brace_pos == -1:
            # No function body found (e.g., forward declaration or incomplete code)
            return start_line
        
        # Find matching closing brace
        depth = 1
        for i in range(brace_pos + 1, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[:i].count('\n')
        
        # Unbalanced braces - incomplete code during editing
        # Return start line to indicate we couldn't determine the end
        return start_line

    def _extract_docstring(self, content: str, func_start: int) -> str | None:
        """Extract documentation comment before a function."""
        # Look backwards for a comment block
        search_start = max(0, func_start - 500)
        prefix = content[search_start:func_start].rstrip()
        
        # Check for /// or /** style comments
        lines = prefix.split('\n')
        doc_lines: list[str] = []
        
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith('///'):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.startswith('*') and not stripped.startswith('*/'):
                doc_lines.insert(0, stripped[1:].strip())
            elif stripped.startswith('/**'):
                doc_lines.insert(0, stripped[3:].strip())
                break
            elif stripped.endswith('*/'):
                doc_lines.insert(0, stripped[:-2].strip())
            elif stripped == '' or stripped.startswith('//'):
                continue
            else:
                # Not a doc comment, stop
                if doc_lines:
                    break
        
        if doc_lines:
            return '\n'.join(doc_lines)
        return None

    def _estimate_shared_mem_size(self, type_str: str, array_size: str | None) -> int | None:
        """Estimate shared memory size in bytes.
        
        Handles both 1D (e.g., [256]) and 2D (e.g., [16][16]) arrays.
        Returns None if size cannot be determined (e.g., non-literal dimension).
        
        Why no eval(): We only handle literal integer dimensions and simple multiplication.
        Variable-based dimensions (e.g., [BLOCK_SIZE]) return None - that's correct behavior
        since we can't know the value at parse time.
        """
        # Size mapping for common types
        type_sizes = {
            'char': 1, 'int8_t': 1, 'uint8_t': 1,
            'short': 2, 'int16_t': 2, 'uint16_t': 2, 'half': 2, '__half': 2,
            'int': 4, 'int32_t': 4, 'uint32_t': 4, 'float': 4, 'unsigned': 4,
            'long': 8, 'int64_t': 8, 'uint64_t': 8, 'double': 8, 'long long': 8,
            'float4': 16, 'float2': 8, 'int4': 16, 'int2': 8,
            'double2': 16, 'double4': 32,
        }
        
        # Find base type
        base_type = type_str.strip()
        type_size: int | None = None
        for known_type, size in type_sizes.items():
            if known_type in base_type:
                type_size = size
                break
        
        if type_size is None:
            return None
        
        if not array_size:
            return type_size
        
        # Parse array dimensions - could be [n] or [n][m]
        # Extract all bracketed dimensions
        dims = re.findall(r'\[([^\]]+)\]', array_size)
        if not dims:
            return type_size
        
        total_elements = 1
        for dim in dims:
            dim_value = self._parse_dimension_expression(dim.strip())
            if dim_value is None:
                # Non-literal dimension (e.g., variable) - cannot determine size
                return None
            total_elements *= dim_value
        
        return type_size * total_elements

    def _parse_dimension_expression(self, expr: str) -> int | None:
        """Parse a dimension expression safely without eval().
        
        Handles:
        - Simple integers: "256"
        - Simple multiplication: "16 * 16", "BLOCK_SIZE * 4" (only if all literal)
        
        Returns None for anything we can't safely parse (variables, complex expressions).
        This is correct behavior - we don't know variable values at parse time.
        """
        expr = expr.strip()
        
        # Simple integer
        if expr.isdigit():
            return int(expr)
        
        # Handle expressions with * (multiplication only)
        if '*' in expr:
            parts = expr.split('*')
            result = 1
            for part in parts:
                part = part.strip()
                if not part.isdigit():
                    # Contains a variable or non-integer - cannot evaluate
                    return None
                result *= int(part)
            return result
        
        # Not a simple literal - could be a variable like BLOCK_SIZE
        return None


def is_hip_file(content: str) -> bool:
    """Check if content appears to be a HIP file based on content markers."""
    hip_markers = [
        '#include <hip/hip_runtime.h>',
        '#include "hip/hip_runtime.h"',
        '#include <hip/hip_runtime_api.h>',
        'hipMalloc',
        'hipMemcpy',
        'hipFree',
        'hipLaunchKernelGGL',
        'hipDeviceSynchronize',
        '__HIP_PLATFORM_AMD__',
        '__HIP_PLATFORM_HCC__',
        'HIP_KERNEL_NAME',
    ]
    
    content_lower = content.lower()
    for marker in hip_markers:
        if marker.lower() in content_lower:
            return True
    
    return False
