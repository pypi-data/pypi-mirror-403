
import re

from lsprotocol.types import InlayHint, InlayHintKind, Position, Range

from ..languages.registry import get_language_registry


# HIP kernel launch pattern: kernel<<<grid, block, shared, stream>>>
HIP_LAUNCH_PATTERN = re.compile(
    r'(\w+)\s*<<<\s*'
    r'([^,>]+)\s*,\s*'  # grid
    r'([^,>]+)'          # block
    r'(?:\s*,\s*([^,>]+))?'  # shared (optional)
    r'(?:\s*,\s*([^>]+))?'   # stream (optional)
    r'\s*>>>'
)

# Shared memory declaration pattern
SHARED_MEM_PATTERN = re.compile(
    r'__shared__\s+([\w\s:<>]+?)\s+(\w+)\s*\[([^\]]+)\]'
)


def handle_inlay_hint(uri: str, content: str, range: Range) -> list[InlayHint]:
    registry = get_language_registry()
    language_info = registry.parse_file(uri, content)

    if not language_info:
        return []

    hints: list[InlayHint] = []
    lines = content.split("\n")

    # Layout hints (CuTeDSL)
    for layout in language_info.layouts:
        if layout.line < range.start.line or layout.line > range.end.line:
            continue

        layout_line = lines[layout.line] if layout.line < len(lines) else ""

        if "=" in layout_line:
            equals_pos = layout_line.find("=")
            hint_text = ": Layout"
            if layout.shape:
                hint_text = f": Layout[Shape{layout.shape}]"

            hint_position = Position(
                line=layout.line,
                character=equals_pos + 1
            )

            hints.append(InlayHint(
                position=hint_position,
                label=hint_text,
                kind=InlayHintKind.Type,
                padding_left=True,
                padding_right=False
            ))

    # Kernel hints (CuTeDSL)
    for kernel in language_info.kernels:
        if kernel.line < range.start.line or kernel.line > range.end.line:
            continue

        kernel_line = lines[kernel.line] if kernel.line < len(lines) else ""

        if "def " in kernel_line and "(" in kernel_line:
            paren_pos = kernel_line.find("(")
            hint_text = " -> Kernel"

            hint_position = Position(
                line=kernel.line,
                character=paren_pos
            )

            hints.append(InlayHint(
                position=hint_position,
                label=hint_text,
                kind=InlayHintKind.Type,
                padding_left=True,
                padding_right=True
            ))

    # HIP/CUDA-specific hints
    if language_info.language in ("hip", "cuda", "cpp"):
        hints.extend(_get_hip_inlay_hints(lines, range))

    return hints


def _get_hip_inlay_hints(lines: list[str], range: Range) -> list[InlayHint]:
    """Generate HIP-specific inlay hints.
    
    - Kernel launch dimension annotations
    - Shared memory size annotations
    """
    hints: list[InlayHint] = []

    for i in range(range.start.line, min(range.end.line + 1, len(lines))):
        line = lines[i]
        
        # Kernel launch hints
        for match in HIP_LAUNCH_PATTERN.finditer(line):
            kernel_name = match.group(1)
            grid_dim = match.group(2).strip()
            block_dim = match.group(3).strip()
            shared_mem = match.group(4)
            stream = match.group(5)
            
            # Add hint after >>> showing launch configuration
            hint_parts = []
            
            # Try to parse and annotate dimensions
            grid_info = _parse_dim(grid_dim)
            block_info = _parse_dim(block_dim)
            
            if grid_info:
                hint_parts.append(f"{grid_info} blocks")
            if block_info:
                hint_parts.append(f"{block_info} threads/block")
                # Calculate wavefronts (AMD uses 64-thread wavefronts)
                try:
                    total_threads = _eval_dim(block_dim)
                    if total_threads:
                        wavefronts = (total_threads + 63) // 64
                        hint_parts.append(f"{wavefronts} wavefront{'s' if wavefronts != 1 else ''}")
                except (ValueError, SyntaxError):
                    pass
            
            if hint_parts:
                hint_text = " // " + ", ".join(hint_parts)
                
                # Position after >>>
                hint_pos = match.end()
                
                hints.append(InlayHint(
                    position=Position(line=i, character=hint_pos),
                    label=hint_text,
                    kind=InlayHintKind.Parameter,
                    padding_left=True,
                    padding_right=False
                ))
        
        # Shared memory size hints
        for match in SHARED_MEM_PATTERN.finditer(line):
            type_str = match.group(1).strip()
            var_name = match.group(2)
            array_size = match.group(3).strip()
            
            size_bytes = _estimate_size(type_str, array_size)
            if size_bytes:
                if size_bytes >= 1024:
                    size_str = f" // {size_bytes / 1024:.1f} KB LDS"
                else:
                    size_str = f" // {size_bytes} bytes LDS"
                
                # Position at end of declaration
                hint_pos = match.end()
                
                hints.append(InlayHint(
                    position=Position(line=i, character=hint_pos),
                    label=size_str,
                    kind=InlayHintKind.Type,
                    padding_left=True,
                    padding_right=False
                ))

    return hints


def _parse_dim(dim_str: str) -> str | None:
    """Parse a dimension string and return a human-readable description."""
    dim_str = dim_str.strip()
    
    # Simple number
    if dim_str.isdigit():
        return dim_str
    
    # dim3(x, y, z)
    if dim_str.startswith("dim3("):
        return dim_str
    
    # Variable or expression
    if re.match(r'^[\w_]+$', dim_str):
        return dim_str
    
    return None


def _eval_dim(dim_str: str) -> int | None:
    """Try to evaluate a dimension to an integer."""
    dim_str = dim_str.strip()
    
    # Simple number
    if dim_str.isdigit():
        return int(dim_str)
    
    # dim3(x) or dim3(x, y) or dim3(x, y, z) - try to multiply
    if dim_str.startswith("dim3(") and dim_str.endswith(")"):
        inner = dim_str[5:-1]
        parts = [p.strip() for p in inner.split(",")]
        try:
            total = 1
            for p in parts:
                if p.isdigit():
                    total *= int(p)
                else:
                    return None  # Can't evaluate variable
            return total
        except (ValueError, SyntaxError):
            return None
    
    return None


def _estimate_size(type_str: str, array_size: str) -> int | None:
    """Estimate size in bytes for a shared memory allocation."""
    type_sizes = {
        'char': 1, 'int8_t': 1, 'uint8_t': 1,
        'short': 2, 'int16_t': 2, 'uint16_t': 2, 'half': 2, '__half': 2,
        'int': 4, 'int32_t': 4, 'uint32_t': 4, 'float': 4, 'unsigned': 4,
        'long': 8, 'int64_t': 8, 'uint64_t': 8, 'double': 8,
        'float4': 16, 'float2': 8, 'int4': 16, 'int2': 8,
        'double2': 16, 'double4': 32,
    }
    
    # Find base type
    base_type = type_str.strip()
    type_size = None
    for known_type, size in type_sizes.items():
        if known_type in base_type:
            type_size = size
            break
    
    if type_size is None:
        type_size = 4  # Default to 4 bytes
    
    # Try to evaluate array size
    try:
        # Handle simple expressions
        arr_size = eval(array_size.replace('*', ' * '))
        return type_size * arr_size
    except (ValueError, SyntaxError, NameError):
        return None
