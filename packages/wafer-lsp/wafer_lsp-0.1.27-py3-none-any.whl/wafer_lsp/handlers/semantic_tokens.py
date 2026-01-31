
import re

from lsprotocol.types import SemanticTokens, SemanticTokensLegend

from ..languages.registry import get_language_registry

TOKEN_TYPES = [
    "kernel",           # 0: GPU kernel functions (__global__)
    "layout",           # 1: Layout variables
    "struct",           # 2: Structs
    "decorator",        # 3: Python decorators (@cute.kernel)
    "keyword_gpu",      # 4: GPU keywords (__global__, __device__, __shared__)
    "keyword_memory",   # 5: Memory qualifiers (__shared__, __constant__)
    "function_hip_api", # 6: HIP API calls (hipMalloc, etc.)
    "function_intrinsic", # 7: Wavefront intrinsics (__shfl, __ballot)
    "device_function",  # 8: __device__ functions
]

TOKEN_MODIFIERS = [
    "definition",
    "declaration",
]

SEMANTIC_TOKENS_LEGEND = SemanticTokensLegend(
    token_types=TOKEN_TYPES,
    token_modifiers=TOKEN_MODIFIERS
)

# HIP-specific patterns for semantic highlighting
HIP_KEYWORD_PATTERN = re.compile(r'\b(__global__|__device__|__host__|__forceinline__)\b')
HIP_MEMORY_KEYWORD_PATTERN = re.compile(r'\b(__shared__|__constant__|__restrict__)\b')
HIP_LAUNCH_BOUNDS_PATTERN = re.compile(r'__launch_bounds__\s*\([^)]+\)')
HIP_API_PATTERN = re.compile(
    r'\b(hipMalloc|hipMallocManaged|hipMallocAsync|hipFree|hipFreeAsync|'
    r'hipMemcpy|hipMemcpyAsync|hipMemset|hipMemsetAsync|'
    r'hipHostMalloc|hipHostFree|hipHostRegister|hipHostUnregister|'
    r'hipDeviceSynchronize|hipStreamSynchronize|'
    r'hipStreamCreate|hipStreamDestroy|hipStreamCreateWithFlags|'
    r'hipEventCreate|hipEventDestroy|hipEventRecord|hipEventSynchronize|hipEventElapsedTime|'
    r'hipSetDevice|hipGetDevice|hipGetDeviceCount|hipGetDeviceProperties|'
    r'hipLaunchKernelGGL|hipLaunchCooperativeKernel|'
    r'hipGetLastError|hipPeekAtLastError|hipGetErrorString|hipGetErrorName)\b'
)
HIP_INTRINSIC_PATTERN = re.compile(
    r'\b(__shfl|__shfl_down|__shfl_up|__shfl_xor|__shfl_sync|'
    r'__ballot|__any|__all|__activemask|'
    r'__syncthreads|__syncwarp|__threadfence|__threadfence_block|__threadfence_system|'
    r'atomicAdd|atomicSub|atomicMax|atomicMin|atomicExch|atomicCAS|atomicAnd|atomicOr|atomicXor|'
    r'__popc|__popcll|__clz|__clzll|__ffs|__ffsll|'
    r'__float2half|__half2float|__float2int_rn|__int2float_rn|'
    r'__ldg|__ldcg|__ldca|__ldcs)\b'
)


def handle_semantic_tokens(uri: str, content: str) -> SemanticTokens:
    registry = get_language_registry()
    language_info = registry.parse_file(uri, content)

    if not language_info:
        return SemanticTokens(data=[])

    # Collect all tokens with their positions
    # We'll sort them later to ensure proper delta calculation
    token_entries: list[tuple[int, int, int, int, int]] = []  # (line, char, length, type, modifier)
    lines = content.split("\n")

    # Add kernel tokens
    for kernel in language_info.kernels:
        if kernel.line >= len(lines):
            continue

        kernel_line = lines[kernel.line]
        name_start = kernel_line.find(kernel.name)

        if name_start >= 0:
            token_entries.append((
                kernel.line,
                name_start,
                len(kernel.name),
                TOKEN_TYPES.index("kernel"),
                0
            ))

    # Add layout tokens
    for layout in language_info.layouts:
        if layout.line >= len(lines):
            continue

        layout_line = lines[layout.line]
        name_start = layout_line.find(layout.name)

        if name_start >= 0:
            token_entries.append((
                layout.line,
                name_start,
                len(layout.name),
                TOKEN_TYPES.index("layout"),
                0
            ))

    # Add struct tokens
    for struct in language_info.structs:
        if struct.line >= len(lines):
            continue

        struct_line = lines[struct.line]
        name_start = struct_line.find(struct.name)

        if name_start >= 0:
            token_entries.append((
                struct.line,
                name_start,
                len(struct.name),
                TOKEN_TYPES.index("struct"),
                0
            ))

    # Add CuTeDSL decorator tokens
    for i, line in enumerate(lines):
        if "@cute.kernel" in line or "@cute.struct" in line:
            decorator_start = line.find("@")
            if decorator_start >= 0:
                decorator_end = line.find(" ", decorator_start)
                if decorator_end == -1:
                    decorator_end = len(line)

                token_entries.append((
                    i,
                    decorator_start,
                    decorator_end - decorator_start,
                    TOKEN_TYPES.index("decorator"),
                    0
                ))

    # Add HIP-specific tokens if this is a HIP or CUDA file
    if language_info.language in ("hip", "cuda", "cpp"):
        token_entries.extend(_get_hip_tokens(lines))

    # Sort tokens by position (line, then character)
    token_entries.sort(key=lambda x: (x[0], x[1]))

    # Convert to delta-encoded format
    tokens: list[int] = []
    prev_line = 0
    prev_char = 0

    for line, char, length, token_type, modifier in token_entries:
        delta_line = line - prev_line
        delta_char = char - (prev_char if delta_line == 0 else 0)

        tokens.extend([
            delta_line,
            delta_char,
            length,
            token_type,
            modifier
        ])

        prev_line = line
        prev_char = char

    return SemanticTokens(data=tokens)


def _get_hip_tokens(lines: list[str]) -> list[tuple[int, int, int, int, int]]:
    """Extract HIP-specific semantic tokens from code.
    
    Returns list of (line, char, length, token_type, modifier) tuples.
    """
    token_entries: list[tuple[int, int, int, int, int]] = []
    
    for i, line in enumerate(lines):
        # GPU keywords (__global__, __device__, etc.)
        for match in HIP_KEYWORD_PATTERN.finditer(line):
            token_entries.append((
                i,
                match.start(),
                len(match.group()),
                TOKEN_TYPES.index("keyword_gpu"),
                0
            ))
        
        # Memory keywords (__shared__, __constant__)
        for match in HIP_MEMORY_KEYWORD_PATTERN.finditer(line):
            token_entries.append((
                i,
                match.start(),
                len(match.group()),
                TOKEN_TYPES.index("keyword_memory"),
                0
            ))
        
        # __launch_bounds__
        for match in HIP_LAUNCH_BOUNDS_PATTERN.finditer(line):
            token_entries.append((
                i,
                match.start(),
                len(match.group()),
                TOKEN_TYPES.index("keyword_gpu"),
                0
            ))
        
        # HIP API functions
        for match in HIP_API_PATTERN.finditer(line):
            token_entries.append((
                i,
                match.start(),
                len(match.group()),
                TOKEN_TYPES.index("function_hip_api"),
                0
            ))
        
        # Wavefront intrinsics
        for match in HIP_INTRINSIC_PATTERN.finditer(line):
            token_entries.append((
                i,
                match.start(),
                len(match.group()),
                TOKEN_TYPES.index("function_intrinsic"),
                0
            ))
    
    return token_entries
