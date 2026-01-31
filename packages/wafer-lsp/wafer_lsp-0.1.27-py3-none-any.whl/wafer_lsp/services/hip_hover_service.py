"""
HIP Hover Service.

Provides rich hover documentation for HIP code including:
- HIP API functions (hipMalloc, hipMemcpy, etc.)
- Memory qualifiers (__device__, __shared__, __constant__)
- Wavefront intrinsics (__shfl, __ballot, etc.)
- Thread indexing (threadIdx, blockIdx, etc.)
- Kernel function information
"""

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position

from ..parsers.hip_parser import (
    HIPKernel,
    HIPDeviceFunction,
    SharedMemoryAllocation,
    KernelLaunchSite,
    HIPParser,
)
from .hip_docs import (
    HIPDocsService,
    HIPAPIDoc,
    MemoryQualifierDoc,
    IntrinsicDoc,
    ThreadIndexDoc,
    create_hip_docs_service,
)


class HIPHoverService:
    """Provides hover documentation for HIP code."""

    def __init__(self, docs_service: HIPDocsService | None = None):
        self._docs = docs_service or create_hip_docs_service()
        self._parser = HIPParser()

    def get_hover(self, content: str, position: Position, uri: str) -> Hover | None:
        """Get hover information for a position in HIP code.
        
        Args:
            content: The document content
            position: The cursor position
            uri: The document URI
            
        Returns:
            Hover information or None
        """
        word = self._get_word_at_position(content, position)
        if not word:
            return None

        # Try different types of hover in order of specificity
        
        # 1. Check for HIP API functions
        api_doc = self._docs.get_api_doc(word)
        if api_doc:
            return self._format_api_hover(api_doc)

        # 2. Check for memory qualifiers (including in context)
        qualifier_doc = self._docs.get_memory_qualifier_doc(word)
        if qualifier_doc:
            return self._format_qualifier_hover(qualifier_doc)

        # 3. Check for intrinsics
        intrinsic_doc = self._docs.get_intrinsic_doc(word)
        if intrinsic_doc:
            return self._format_intrinsic_hover(intrinsic_doc)

        # 4. Check for thread indexing variables
        thread_doc = self._docs.get_thread_index_doc(word)
        if thread_doc:
            return self._format_thread_index_hover(thread_doc)

        # 5. Check for kernels/device functions in the file
        parsed = self._parser.parse_file(content)
        
        for kernel in parsed.get("kernels", []):
            if kernel.name == word:
                return self._format_kernel_hover(kernel)

        for device_func in parsed.get("device_functions", []):
            if device_func.name == word:
                return self._format_device_function_hover(device_func)

        # 6. Check for shared memory variables
        for shared_var in parsed.get("shared_memory", []):
            if shared_var.name == word:
                return self._format_shared_memory_hover(shared_var)

        # 7. Check for kernel launch (when hovering on kernel name at launch site)
        for launch in parsed.get("launch_sites", []):
            if launch.kernel_name == word and position.line == launch.line:
                return self._format_launch_site_hover(launch)

        return None

    def _get_word_at_position(self, content: str, position: Position) -> str:
        """Extract the word at the given position."""
        lines = content.split("\n")
        if position.line >= len(lines):
            return ""

        line = lines[position.line]
        if position.character >= len(line):
            return ""

        # Find word boundaries (include underscores for __global__ etc.)
        start = position.character
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1

        end = position.character
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1

        return line[start:end]

    def _format_api_hover(self, doc: HIPAPIDoc) -> Hover:
        """Format hover content for a HIP API function."""
        lines = [
            f"### `{doc.name}`",
            "",
            f"```cpp",
            doc.signature,
            "```",
            "",
            doc.description,
            "",
        ]

        if doc.parameters:
            lines.append("**Parameters:**")
            for param_name, param_desc in doc.parameters:
                lines.append(f"- `{param_name}`: {param_desc}")
            lines.append("")

        lines.append(f"**Returns:** {doc.return_value}")
        lines.append("")

        if doc.amd_notes:
            lines.append("**AMD Notes:**")
            lines.append(f"> {doc.amd_notes}")
            lines.append("")

        if doc.example:
            lines.append("**Example:**")
            lines.append("```cpp")
            lines.extend(doc.example.replace("\\n", "\n").split("\n"))
            lines.append("```")
            lines.append("")

        if doc.related:
            lines.append(f"**Related:** {', '.join(f'`{r}`' for r in doc.related)}")

        if doc.doc_url:
            lines.append("")
            lines.append(f"[📖 Documentation]({doc.doc_url})")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_qualifier_hover(self, doc: MemoryQualifierDoc) -> Hover:
        """Format hover content for a memory qualifier."""
        lines = [
            f"### `{doc.name}`",
            "",
            doc.description,
            "",
            "**AMD Architecture:**",
            doc.amd_details,
            "",
            "**Performance Tips:**",
            doc.performance_tips,
        ]

        if doc.example:
            lines.append("")
            lines.append("**Example:**")
            lines.append("```cpp")
            lines.extend(doc.example.split("\n"))
            lines.append("```")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_intrinsic_hover(self, doc: IntrinsicDoc) -> Hover:
        """Format hover content for a wavefront intrinsic."""
        lines = [
            f"### `{doc.name}`",
            "",
            f"```cpp",
            doc.signature,
            "```",
            "",
            doc.description,
            "",
            "**⚠️ AMD Wavefront Behavior:**",
            f"> {doc.amd_behavior}",
            "",
        ]

        if doc.parameters:
            lines.append("**Parameters:**")
            for param_name, param_desc in doc.parameters:
                lines.append(f"- `{param_name}`: {param_desc}")
            lines.append("")

        lines.append(f"**Returns:** {doc.return_value}")
        lines.append("")

        if doc.example:
            lines.append("**Example:**")
            lines.append("```cpp")
            lines.extend(doc.example.replace("\\n", "\n").split("\n"))
            lines.append("```")
            lines.append("")

        if doc.cuda_equivalent:
            lines.append(f"**CUDA Equivalent:** `{doc.cuda_equivalent}`")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_thread_index_hover(self, doc: ThreadIndexDoc) -> Hover:
        """Format hover content for thread indexing variables."""
        lines = [
            f"### `{doc.name}`",
            "",
            doc.description,
            "",
            "**AMD Context:**",
            f"> {doc.amd_context}",
            "",
        ]

        if doc.common_patterns:
            lines.append("**Common Patterns:**")
            lines.append("```cpp")
            for pattern in doc.common_patterns:
                lines.append(pattern)
            lines.append("```")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_kernel_hover(self, kernel: HIPKernel) -> Hover:
        """Format hover content for a kernel function."""
        lines = [
            f"### 🚀 HIP Kernel: `{kernel.name}`",
            "",
        ]

        if kernel.docstring:
            lines.append(kernel.docstring)
            lines.append("")

        # Build signature
        params_str = ", ".join(kernel.parameters) if kernel.parameters else ""
        lines.append("```cpp")
        if kernel.attributes:
            for attr in kernel.attributes:
                lines.append(attr)
        lines.append(f"__global__ void {kernel.name}({params_str})")
        lines.append("```")
        lines.append("")

        if kernel.parameter_info:
            lines.append("**Parameters:**")
            for param in kernel.parameter_info:
                type_info = f" (`{param.type_str}`)" if param.type_str else ""
                lines.append(f"- `{param.name}`{type_info}")
            lines.append("")

        lines.append(f"**Location:** Lines {kernel.line + 1} - {kernel.end_line + 1}")
        lines.append("")
        lines.append("**AMD GPU Execution:**")
        lines.append("- Executed on GPU Compute Units")
        lines.append("- Threads grouped into 64-thread wavefronts (CDNA)")
        lines.append("- Use `<<<grid, block>>>` or `hipLaunchKernelGGL` to launch")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_device_function_hover(self, func: HIPDeviceFunction) -> Hover:
        """Format hover content for a device function."""
        lines = [
            f"### ⚡ Device Function: `{func.name}`",
            "",
        ]

        # Build signature
        params_str = ", ".join(func.parameters) if func.parameters else ""
        inline_str = "__forceinline__ " if func.is_inline else ""
        lines.append("```cpp")
        lines.append(f"__device__ {inline_str}{func.return_type} {func.name}({params_str})")
        lines.append("```")
        lines.append("")

        if func.parameter_info:
            lines.append("**Parameters:**")
            for param in func.parameter_info:
                type_info = f" (`{param.type_str}`)" if param.type_str else ""
                lines.append(f"- `{param.name}`{type_info}")
            lines.append("")

        lines.append(f"**Returns:** `{func.return_type}`")
        lines.append("")
        lines.append(f"**Location:** Lines {func.line + 1} - {func.end_line + 1}")
        lines.append("")
        lines.append("**Note:** Device functions can only be called from kernel or other device functions.")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_shared_memory_hover(self, shared: SharedMemoryAllocation) -> Hover:
        """Format hover content for a shared memory allocation."""
        lines = [
            f"### 📦 Shared Memory (LDS): `{shared.name}`",
            "",
            f"**Type:** `{shared.type_str}`",
        ]

        if shared.array_size:
            lines.append(f"**Array Size:** `[{shared.array_size}]`")

        if shared.size_bytes:
            if shared.size_bytes >= 1024:
                size_str = f"{shared.size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{shared.size_bytes} bytes"
            lines.append(f"**Size:** {size_str}")

        if shared.is_dynamic:
            lines.append("**Allocation:** Dynamic (extern)")
        else:
            lines.append("**Allocation:** Static")

        lines.append("")
        lines.append("**AMD LDS Details:**")
        lines.append("- On-chip memory with ~100x lower latency than HBM")
        lines.append("- 64 KB per Compute Unit")
        lines.append("- Shared by all threads in the block")
        lines.append("- 32 banks of 4 bytes each")
        lines.append("")
        lines.append("💡 **Tip:** Avoid bank conflicts by using padding: `[SIZE + 1]`")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _format_launch_site_hover(self, launch: KernelLaunchSite) -> Hover:
        """Format hover content for a kernel launch site."""
        lines = [
            f"### 🎯 Kernel Launch: `{launch.kernel_name}`",
            "",
        ]

        if launch.is_hip_launch_kernel_ggl:
            lines.append("**Launch Method:** `hipLaunchKernelGGL`")
        else:
            lines.append("**Launch Method:** `<<<>>>` syntax")

        lines.append("")

        if launch.grid_dim:
            lines.append(f"**Grid Dimensions:** `{launch.grid_dim}`")
        if launch.block_dim:
            lines.append(f"**Block Dimensions:** `{launch.block_dim}`")
            # Try to parse block dimensions for wavefront info
            self._add_wavefront_info(lines, launch.block_dim)

        if launch.shared_mem_bytes:
            lines.append(f"**Dynamic Shared Memory:** `{launch.shared_mem_bytes}`")
        if launch.stream:
            lines.append(f"**Stream:** `{launch.stream}`")

        return Hover(contents=MarkupContent(
            kind=MarkupKind.Markdown,
            value="\n".join(lines)
        ))

    def _add_wavefront_info(self, lines: list[str], block_dim: str) -> None:
        """Add wavefront information based on block dimensions.
        
        Only adds info when block_dim is a simple numeric literal we can parse.
        For complex expressions (variables, dim3, etc.), we don't display wavefront count
        because we can't determine the value at parse time.
        """
        # Only handle simple numeric block size - we don't guess at complex expressions
        if block_dim.isdigit():
            block_size = int(block_dim)
            wavefronts = (block_size + 63) // 64
            lines.append(f"**Wavefronts per Block:** {wavefronts} (64 threads each on CDNA)")


def create_hip_hover_service(docs_service: HIPDocsService | None = None) -> HIPHoverService:
    """Create a HIP hover service instance."""
    return HIPHoverService(docs_service)
