
from lsprotocol.types import DocumentSymbol, Position, Range, SymbolKind

from ..languages.registry import get_language_registry


def handle_document_symbol(uri: str, content: str) -> list[DocumentSymbol]:
    registry = get_language_registry()
    language_info = registry.parse_file(uri, content)

    if not language_info:
        return []

    symbols: list[DocumentSymbol] = []
    lines = content.split("\n")

    # Kernels
    for kernel in language_info.kernels:
        kernel_line = lines[kernel.line] if kernel.line < len(lines) else ""
        name_start = kernel_line.find(kernel.name)
        name_end = name_start + len(kernel.name) if name_start >= 0 else 0

        selection_range = Range(
            start=Position(line=kernel.line, character=max(0, name_start)),
            end=Position(line=kernel.line, character=name_end)
        )
        full_range = Range(
            start=Position(line=kernel.line, character=0),
            end=Position(line=min(kernel.line + 10, len(lines) - 1), character=0)
        )

        # Different detail based on language
        if kernel.language == "hip":
            detail = "🚀 HIP Kernel (AMD GPU)"
        elif kernel.language in ("cuda", "cpp"):
            detail = "🚀 CUDA Kernel"
        else:
            detail = f"GPU Kernel ({registry.get_language_name(kernel.language)})"

        symbols.append(DocumentSymbol(
            name=kernel.name,
            kind=SymbolKind.Function,
            range=full_range,
            selection_range=selection_range,
            detail=detail,
        ))

    # Layouts (CuTeDSL)
    for layout in language_info.layouts:
        layout_line = lines[layout.line] if layout.line < len(lines) else ""
        name_start = layout_line.find(layout.name)
        name_end = name_start + len(layout.name) if name_start >= 0 else 0

        detail = f"Layout: {layout.shape}" if layout.shape else "Layout"

        selection_range = Range(
            start=Position(line=layout.line, character=max(0, name_start)),
            end=Position(line=layout.line, character=name_end)
        )
        full_range = Range(
            start=Position(line=layout.line, character=0),
            end=Position(line=layout.line, character=len(layout_line))
        )

        symbols.append(DocumentSymbol(
            name=layout.name,
            kind=SymbolKind.Variable,
            range=full_range,
            selection_range=selection_range,
            detail=detail,
        ))

    # Structs
    for struct in language_info.structs:
        struct_line = lines[struct.line] if struct.line < len(lines) else ""
        name_start = struct_line.find(struct.name)
        name_end = name_start + len(struct.name) if name_start >= 0 else 0

        selection_range = Range(
            start=Position(line=struct.line, character=max(0, name_start)),
            end=Position(line=struct.line, character=name_end)
        )
        full_range = Range(
            start=Position(line=struct.line, character=0),
            end=Position(line=min(struct.line + 10, len(lines) - 1), character=0)
        )

        symbols.append(DocumentSymbol(
            name=struct.name,
            kind=SymbolKind.Struct,
            range=full_range,
            selection_range=selection_range,
            detail=f"Struct ({registry.get_language_name(struct.language)})",
        ))

    # HIP-specific: Device functions and shared memory
    if language_info.language in ("hip", "cuda", "cpp"):
        symbols.extend(_get_hip_symbols(language_info.raw_data, lines))

    return symbols


def _get_hip_symbols(raw_data: dict, lines: list[str]) -> list[DocumentSymbol]:
    """Extract HIP-specific symbols: device functions, shared memory allocations."""
    symbols: list[DocumentSymbol] = []
    
    # Device functions (from HIP parser)
    device_functions = raw_data.get("device_functions", [])
    for func in device_functions:
        if not hasattr(func, "line") or not hasattr(func, "name"):
            continue
            
        func_line = lines[func.line] if func.line < len(lines) else ""
        name_start = func_line.find(func.name)
        name_end = name_start + len(func.name) if name_start >= 0 else 0
        
        end_line = getattr(func, "end_line", func.line + 10)
        
        selection_range = Range(
            start=Position(line=func.line, character=max(0, name_start)),
            end=Position(line=func.line, character=name_end)
        )
        full_range = Range(
            start=Position(line=func.line, character=0),
            end=Position(line=min(end_line, len(lines) - 1), character=0)
        )
        
        return_type = getattr(func, "return_type", "void")
        detail = f"⚡ Device Function -> {return_type}"
        
        symbols.append(DocumentSymbol(
            name=func.name,
            kind=SymbolKind.Method,
            range=full_range,
            selection_range=selection_range,
            detail=detail,
        ))
    
    # Shared memory allocations
    shared_memory = raw_data.get("shared_memory", [])
    for shared in shared_memory:
        if not hasattr(shared, "line") or not hasattr(shared, "name"):
            continue
            
        shared_line = lines[shared.line] if shared.line < len(lines) else ""
        name_start = shared_line.find(shared.name)
        name_end = name_start + len(shared.name) if name_start >= 0 else 0
        
        selection_range = Range(
            start=Position(line=shared.line, character=max(0, name_start)),
            end=Position(line=shared.line, character=name_end)
        )
        full_range = Range(
            start=Position(line=shared.line, character=0),
            end=Position(line=shared.line, character=len(shared_line))
        )
        
        type_str = getattr(shared, "type_str", "")
        size_bytes = getattr(shared, "size_bytes", None)
        if size_bytes:
            if size_bytes >= 1024:
                detail = f"📦 __shared__ {type_str} ({size_bytes / 1024:.1f} KB)"
            else:
                detail = f"📦 __shared__ {type_str} ({size_bytes} bytes)"
        else:
            detail = f"📦 __shared__ {type_str}"
        
        symbols.append(DocumentSymbol(
            name=shared.name,
            kind=SymbolKind.Variable,
            range=full_range,
            selection_range=selection_range,
            detail=detail,
        ))
    
    return symbols
