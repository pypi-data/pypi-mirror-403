"""
HIP API Documentation Database.

Comprehensive documentation for HIP (AMD GPU) APIs, intrinsics,
memory qualifiers, and AMD architecture-specific information.

This enables rich hover documentation for developers writing HIP kernels
without needing to constantly reference external ROCm documentation.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HIPAPIDoc:
    """Documentation for a HIP API function."""
    name: str
    signature: str
    description: str
    parameters: list[tuple[str, str]]  # (param_name, description)
    return_value: str
    amd_notes: str | None = None  # AMD-specific behavior notes
    example: str | None = None
    related: list[str] = field(default_factory=list)
    doc_url: str | None = None


@dataclass(frozen=True)
class MemoryQualifierDoc:
    """Documentation for a memory qualifier."""
    name: str
    description: str
    amd_details: str
    performance_tips: str
    example: str | None = None


@dataclass(frozen=True)
class IntrinsicDoc:
    """Documentation for a wavefront/warp intrinsic."""
    name: str
    signature: str
    description: str
    amd_behavior: str  # AMD-specific behavior (especially wavefront size)
    parameters: list[tuple[str, str]]
    return_value: str
    example: str | None = None
    cuda_equivalent: str | None = None


@dataclass(frozen=True)
class ThreadIndexDoc:
    """Documentation for thread indexing variables."""
    name: str
    description: str
    amd_context: str
    common_patterns: list[str]


# ============================================================================
# HIP Runtime API Documentation
# ============================================================================

HIP_API_DOCS: dict[str, HIPAPIDoc] = {
    # Memory Management
    "hipMalloc": HIPAPIDoc(
        name="hipMalloc",
        signature="hipError_t hipMalloc(void** ptr, size_t size)",
        description="Allocates device memory.",
        parameters=[
            ("ptr", "Pointer to allocated device memory"),
            ("size", "Requested allocation size in bytes"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Memory is allocated on the currently active GPU. For multi-GPU systems, use hipSetDevice() first.",
        example='float* d_data;\\nhipMalloc(&d_data, N * sizeof(float));',
        related=["hipFree", "hipMallocManaged", "hipMallocAsync"],
        doc_url="https://rocm.docs.amd.com/projects/HIP/en/latest/reference/hip_runtime_api.html",
    ),
    "hipMallocManaged": HIPAPIDoc(
        name="hipMallocManaged",
        signature="hipError_t hipMallocManaged(void** devPtr, size_t size, unsigned int flags = hipMemAttachGlobal)",
        description="Allocates managed memory accessible from both host and device.",
        parameters=[
            ("devPtr", "Pointer to allocated managed memory"),
            ("size", "Requested allocation size in bytes"),
            ("flags", "Memory attachment flags (hipMemAttachGlobal or hipMemAttachHost)"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Unified memory on AMD GPUs uses page migration. Performance may differ from explicit memory management depending on access patterns.",
        example='float* data;\\nhipMallocManaged(&data, N * sizeof(float));',
        related=["hipMalloc", "hipFree", "hipMemPrefetchAsync"],
    ),
    "hipMallocAsync": HIPAPIDoc(
        name="hipMallocAsync",
        signature="hipError_t hipMallocAsync(void** devPtr, size_t size, hipStream_t stream)",
        description="Allocates device memory asynchronously in a stream.",
        parameters=[
            ("devPtr", "Pointer to allocated device memory"),
            ("size", "Requested allocation size in bytes"),
            ("stream", "Stream to use for allocation"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Uses HIP's stream-ordered memory allocator for better performance in streaming workloads.",
        related=["hipFreeAsync", "hipMalloc"],
    ),
    "hipFree": HIPAPIDoc(
        name="hipFree",
        signature="hipError_t hipFree(void* ptr)",
        description="Frees device memory.",
        parameters=[
            ("ptr", "Device pointer to free"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Synchronizes the device before freeing. Use hipFreeAsync() for non-blocking free.",
        related=["hipMalloc", "hipFreeAsync"],
    ),
    "hipFreeAsync": HIPAPIDoc(
        name="hipFreeAsync",
        signature="hipError_t hipFreeAsync(void* devPtr, hipStream_t stream)",
        description="Frees device memory asynchronously in a stream.",
        parameters=[
            ("devPtr", "Device pointer to free"),
            ("stream", "Stream to use for deallocation"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipMallocAsync", "hipFree"],
    ),

    # Memory Copy
    "hipMemcpy": HIPAPIDoc(
        name="hipMemcpy",
        signature="hipError_t hipMemcpy(void* dst, const void* src, size_t sizeBytes, hipMemcpyKind kind)",
        description="Copies data between host and device memory.",
        parameters=[
            ("dst", "Destination memory address"),
            ("src", "Source memory address"),
            ("sizeBytes", "Size of memory copy in bytes"),
            ("kind", "Type of transfer: hipMemcpyHostToDevice, hipMemcpyDeviceToHost, hipMemcpyDeviceToDevice, hipMemcpyHostToHost"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="This is a synchronous operation. For async transfers, use hipMemcpyAsync().",
        example='hipMemcpy(d_data, h_data, N * sizeof(float), hipMemcpyHostToDevice);',
        related=["hipMemcpyAsync", "hipMemcpy2D", "hipMemcpy3D"],
    ),
    "hipMemcpyAsync": HIPAPIDoc(
        name="hipMemcpyAsync",
        signature="hipError_t hipMemcpyAsync(void* dst, const void* src, size_t sizeBytes, hipMemcpyKind kind, hipStream_t stream)",
        description="Copies data between host and device memory asynchronously.",
        parameters=[
            ("dst", "Destination memory address"),
            ("src", "Source memory address"),
            ("sizeBytes", "Size of memory copy in bytes"),
            ("kind", "Type of transfer"),
            ("stream", "Stream for async execution"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="For best performance with async copies, use pinned host memory allocated with hipHostMalloc().",
        related=["hipMemcpy", "hipHostMalloc"],
    ),
    "hipMemset": HIPAPIDoc(
        name="hipMemset",
        signature="hipError_t hipMemset(void* dst, int value, size_t sizeBytes)",
        description="Fills device memory with a constant byte value.",
        parameters=[
            ("dst", "Pointer to device memory"),
            ("value", "Value to set (only the lowest byte is used)"),
            ("sizeBytes", "Number of bytes to set"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipMemsetAsync", "hipMemset2D"],
    ),
    "hipMemsetAsync": HIPAPIDoc(
        name="hipMemsetAsync",
        signature="hipError_t hipMemsetAsync(void* dst, int value, size_t sizeBytes, hipStream_t stream)",
        description="Fills device memory with a constant byte value asynchronously.",
        parameters=[
            ("dst", "Pointer to device memory"),
            ("value", "Value to set (only the lowest byte is used)"),
            ("sizeBytes", "Number of bytes to set"),
            ("stream", "Stream for async execution"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipMemset"],
    ),

    # Pinned Memory
    "hipHostMalloc": HIPAPIDoc(
        name="hipHostMalloc",
        signature="hipError_t hipHostMalloc(void** ptr, size_t size, unsigned int flags = hipHostMallocDefault)",
        description="Allocates pinned (page-locked) host memory.",
        parameters=[
            ("ptr", "Pointer to allocated host memory"),
            ("size", "Requested allocation size in bytes"),
            ("flags", "Allocation flags (hipHostMallocDefault, hipHostMallocPortable, hipHostMallocMapped, hipHostMallocWriteCombined)"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Pinned memory enables faster DMA transfers and is required for async memory copies. Use sparingly as it reduces available system memory.",
        example='float* h_pinned;\\nhipHostMalloc(&h_pinned, N * sizeof(float), hipHostMallocDefault);',
        related=["hipHostFree", "hipMemcpyAsync"],
    ),
    "hipHostFree": HIPAPIDoc(
        name="hipHostFree",
        signature="hipError_t hipHostFree(void* ptr)",
        description="Frees pinned host memory.",
        parameters=[
            ("ptr", "Host pointer to free"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipHostMalloc"],
    ),

    # Synchronization
    "hipDeviceSynchronize": HIPAPIDoc(
        name="hipDeviceSynchronize",
        signature="hipError_t hipDeviceSynchronize(void)",
        description="Blocks until the device has completed all preceding requested tasks.",
        parameters=[],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="This is a heavy synchronization point. For stream-level sync, use hipStreamSynchronize(). For event-based sync, use hipEventSynchronize().",
        related=["hipStreamSynchronize", "hipEventSynchronize"],
    ),
    "hipStreamSynchronize": HIPAPIDoc(
        name="hipStreamSynchronize",
        signature="hipError_t hipStreamSynchronize(hipStream_t stream)",
        description="Blocks until the stream has completed all operations.",
        parameters=[
            ("stream", "Stream to synchronize"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="More efficient than hipDeviceSynchronize() when only one stream needs to complete.",
        related=["hipDeviceSynchronize", "hipStreamWaitEvent"],
    ),

    # Streams
    "hipStreamCreate": HIPAPIDoc(
        name="hipStreamCreate",
        signature="hipError_t hipStreamCreate(hipStream_t* stream)",
        description="Creates a new asynchronous stream.",
        parameters=[
            ("stream", "Pointer to new stream"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="AMD GPUs can execute multiple streams concurrently on different compute units. Use streams for overlapping compute and memory transfers.",
        related=["hipStreamDestroy", "hipStreamCreateWithFlags"],
    ),
    "hipStreamDestroy": HIPAPIDoc(
        name="hipStreamDestroy",
        signature="hipError_t hipStreamDestroy(hipStream_t stream)",
        description="Destroys an asynchronous stream.",
        parameters=[
            ("stream", "Stream to destroy"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipStreamCreate"],
    ),

    # Events
    "hipEventCreate": HIPAPIDoc(
        name="hipEventCreate",
        signature="hipError_t hipEventCreate(hipEvent_t* event)",
        description="Creates an event.",
        parameters=[
            ("event", "Pointer to new event"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipEventDestroy", "hipEventRecord", "hipEventSynchronize"],
    ),
    "hipEventRecord": HIPAPIDoc(
        name="hipEventRecord",
        signature="hipError_t hipEventRecord(hipEvent_t event, hipStream_t stream)",
        description="Records an event in a stream.",
        parameters=[
            ("event", "Event to record"),
            ("stream", "Stream in which to record (0 for default stream)"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipEventCreate", "hipEventElapsedTime"],
    ),
    "hipEventSynchronize": HIPAPIDoc(
        name="hipEventSynchronize",
        signature="hipError_t hipEventSynchronize(hipEvent_t event)",
        description="Blocks until the event has been recorded.",
        parameters=[
            ("event", "Event to wait for"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipEventRecord", "hipStreamWaitEvent"],
    ),
    "hipEventElapsedTime": HIPAPIDoc(
        name="hipEventElapsedTime",
        signature="hipError_t hipEventElapsedTime(float* ms, hipEvent_t start, hipEvent_t stop)",
        description="Computes the elapsed time between two events.",
        parameters=[
            ("ms", "Pointer to elapsed time in milliseconds"),
            ("start", "Starting event"),
            ("stop", "Ending event"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        example='hipEventRecord(start, stream);\\nkernel<<<...>>>();\\nhipEventRecord(stop, stream);\\nhipEventSynchronize(stop);\\nfloat ms;\\nhipEventElapsedTime(&ms, start, stop);',
        related=["hipEventCreate", "hipEventRecord"],
    ),

    # Device Management
    "hipSetDevice": HIPAPIDoc(
        name="hipSetDevice",
        signature="hipError_t hipSetDevice(int deviceId)",
        description="Sets the current device for the calling thread.",
        parameters=[
            ("deviceId", "Device ID to use"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Required before allocating memory in multi-GPU setups. Each thread can have its own active device.",
        related=["hipGetDevice", "hipGetDeviceCount"],
    ),
    "hipGetDevice": HIPAPIDoc(
        name="hipGetDevice",
        signature="hipError_t hipGetDevice(int* deviceId)",
        description="Gets the current device for the calling thread.",
        parameters=[
            ("deviceId", "Pointer to device ID"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipSetDevice"],
    ),
    "hipGetDeviceCount": HIPAPIDoc(
        name="hipGetDeviceCount",
        signature="hipError_t hipGetDeviceCount(int* count)",
        description="Returns the number of available HIP devices.",
        parameters=[
            ("count", "Pointer to device count"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        related=["hipSetDevice", "hipGetDeviceProperties"],
    ),
    "hipGetDeviceProperties": HIPAPIDoc(
        name="hipGetDeviceProperties",
        signature="hipError_t hipGetDeviceProperties(hipDeviceProp_t* prop, int deviceId)",
        description="Returns device properties.",
        parameters=[
            ("prop", "Pointer to device properties struct"),
            ("deviceId", "Device ID"),
        ],
        return_value="hipSuccess on success, or an error code on failure",
        amd_notes="Key properties for AMD GPUs: warpSize (64 for CDNA), maxSharedMemoryPerBlock, multiProcessorCount (compute units), gcnArchName.",
        related=["hipGetDeviceCount"],
    ),

    # Kernel Launch
    "hipLaunchKernelGGL": HIPAPIDoc(
        name="hipLaunchKernelGGL",
        signature="void hipLaunchKernelGGL(F kernel, dim3 gridDim, dim3 blockDim, size_t sharedMem, hipStream_t stream, Args... args)",
        description="Launches a kernel using HIP's macro syntax.",
        parameters=[
            ("kernel", "Kernel function to launch"),
            ("gridDim", "Grid dimensions (number of blocks)"),
            ("blockDim", "Block dimensions (threads per block)"),
            ("sharedMem", "Dynamic shared memory size in bytes"),
            ("stream", "Stream for async execution (0 for default)"),
            ("args", "Kernel arguments"),
        ],
        return_value="void",
        amd_notes="Alternative to <<<>>> syntax. Provides better compile-time checking and is the native HIP way to launch kernels.",
        example='hipLaunchKernelGGL(myKernel, dim3(gridSize), dim3(blockSize), 0, stream, arg1, arg2);',
        related=["hipLaunchCooperativeKernel"],
    ),

    # Error Handling
    "hipGetLastError": HIPAPIDoc(
        name="hipGetLastError",
        signature="hipError_t hipGetLastError(void)",
        description="Returns the last error from a HIP runtime call and resets it to hipSuccess.",
        parameters=[],
        return_value="Last error code",
        amd_notes="Use after kernel launches to check for launch errors. Kernel launches are asynchronous, so errors may appear on subsequent sync operations.",
        related=["hipPeekAtLastError", "hipGetErrorString"],
    ),
    "hipGetErrorString": HIPAPIDoc(
        name="hipGetErrorString",
        signature="const char* hipGetErrorString(hipError_t error)",
        description="Returns a string description of an error code.",
        parameters=[
            ("error", "HIP error code"),
        ],
        return_value="Pointer to error string",
        example='hipError_t err = hipGetLastError();\\nif (err != hipSuccess) printf("Error: %s\\n", hipGetErrorString(err));',
        related=["hipGetLastError"],
    ),
}

# ============================================================================
# Memory Qualifier Documentation
# ============================================================================

MEMORY_QUALIFIER_DOCS: dict[str, MemoryQualifierDoc] = {
    "__device__": MemoryQualifierDoc(
        name="__device__",
        description="Declares a variable that resides in device (global) memory, or marks a function as callable only from device code.",
        amd_details="On AMD GPUs, __device__ variables reside in HBM (High Bandwidth Memory) with ~1-2 TB/s bandwidth on MI300X. Access latency is ~400-600 cycles.",
        performance_tips="• Coalesce accesses: adjacent threads should access adjacent memory\\n• Use vectorized loads (float4, etc.) when possible\\n• Consider __shared__ for frequently accessed data",
        example='__device__ float global_array[1024];\\n\\n__device__ float helper_function(float x) {\\n    return x * x;\\n}',
    ),
    "__shared__": MemoryQualifierDoc(
        name="__shared__",
        description="Declares a variable in Local Data Share (LDS) memory, shared by all threads in a block.",
        amd_details="On AMD CDNA GPUs:\\n• LDS is on-chip memory with ~100x lower latency than global memory\\n• 64 KB per Compute Unit (shared across all active wavefronts)\\n• Organized in 32 banks of 4 bytes each\\n• Shared across all 64 threads in a wavefront",
        performance_tips="• Avoid bank conflicts by having threads access different banks\\n• Use padding for arrays: float data[32][33] instead of float data[32][32]\\n• LDS is a limited resource - high usage reduces occupancy",
        example='__shared__ float tile[BLOCK_SIZE][BLOCK_SIZE];\\n\\n// With padding to avoid bank conflicts\\n__shared__ float tile_padded[BLOCK_SIZE][BLOCK_SIZE + 1];',
    ),
    "__constant__": MemoryQualifierDoc(
        name="__constant__",
        description="Declares a variable in constant memory, which is cached and read-only from device code.",
        amd_details="On AMD GPUs, constant memory is cached in the L1/L2 cache hierarchy. All threads reading the same address get the data broadcast efficiently.",
        performance_tips="• Best for data that all threads read (e.g., coefficients, lookup tables)\\n• Limited to 64 KB total\\n• Writes must happen from host before kernel launch",
        example='__constant__ float filter_coefficients[256];',
    ),
    "__global__": MemoryQualifierDoc(
        name="__global__",
        description="Declares a function as a GPU kernel that can be launched from host code.",
        amd_details="On AMD GPUs, kernels are compiled to AMDGPU ISA and executed on Compute Units. Each CU has 64 SIMD lanes (wavefront size of 64 threads).",
        performance_tips="• Use __launch_bounds__ to hint the compiler about resource usage\\n• Consider grid-stride loops for flexibility\\n• Profile with rocprof to identify bottlenecks",
        example='__global__ void vector_add(float* a, float* b, float* c, int n) {\\n    int idx = blockIdx.x * blockDim.x + threadIdx.x;\\n    if (idx < n) c[idx] = a[idx] + b[idx];\\n}',
    ),
    "__host__": MemoryQualifierDoc(
        name="__host__",
        description="Declares a function as callable from host code. This is the default for functions.",
        amd_details="Can be combined with __device__ to compile a function for both host and device.",
        performance_tips="Use __host__ __device__ for utility functions that work on both CPU and GPU.",
        example='__host__ __device__ float utility_func(float x) {\\n    return sqrtf(x);\\n}',
    ),
    "__launch_bounds__": MemoryQualifierDoc(
        name="__launch_bounds__",
        description="Specifies the maximum number of threads per block and optionally minimum blocks per multiprocessor.",
        amd_details="Helps the AMD GPU compiler optimize register allocation. On CDNA, each CU has 65536 32-bit registers shared among wavefronts.",
        performance_tips="• Set maxThreadsPerBlock to your actual block size\\n• Higher minBlocksPerMultiprocessor increases occupancy but limits registers per thread\\n• Profile different configurations to find optimal settings",
        example='__global__ __launch_bounds__(256, 4)\\nvoid my_kernel(...) {\\n    // Max 256 threads/block, at least 4 blocks/CU\\n}',
    ),
    "__restrict__": MemoryQualifierDoc(
        name="__restrict__",
        description="Hints that a pointer is the only way to access the pointed-to memory (no aliasing).",
        amd_details="Enables the compiler to perform more aggressive optimizations by assuming no pointer aliasing.",
        performance_tips="• Use on kernel parameters when pointers don't overlap\\n• Can significantly improve memory access scheduling",
        example='__global__ void kernel(float* __restrict__ input, float* __restrict__ output) {\\n    // Compiler knows input and output don\'t overlap\\n}',
    ),
}

# ============================================================================
# Wavefront Intrinsic Documentation
# ============================================================================

INTRINSIC_DOCS: dict[str, IntrinsicDoc] = {
    # Shuffle operations
    "__shfl": IntrinsicDoc(
        name="__shfl",
        signature="T __shfl(T var, int srcLane, int width = warpSize)",
        description="Reads a variable from another lane in the wavefront.",
        amd_behavior="On AMD GPUs, operates on 64-thread wavefronts (CDNA) or 32/64 (RDNA). The width parameter defaults to 64. No mask parameter - all lanes participate.",
        parameters=[
            ("var", "Value to share"),
            ("srcLane", "Lane to read from (0-63 on CDNA)"),
            ("width", "Logical wavefront width (default: warpSize = 64)"),
        ],
        return_value="Value from the source lane",
        example='// Broadcast lane 0 to all lanes\\nfloat val = __shfl(my_val, 0);',
        cuda_equivalent="__shfl_sync(0xFFFFFFFFFFFFFFFF, var, srcLane, width)",
    ),
    "__shfl_down": IntrinsicDoc(
        name="__shfl_down",
        signature="T __shfl_down(T var, unsigned int delta, int width = warpSize)",
        description="Reads a variable from a lane with higher index (lane + delta).",
        amd_behavior="On AMD CDNA, operates on 64-thread wavefronts. Common for reductions: each lane reads from lane + delta. For warp reduction, loop from delta=32 down to delta=1.",
        parameters=[
            ("var", "Value to share"),
            ("delta", "Offset to add to current lane ID"),
            ("width", "Logical wavefront width (default: 64)"),
        ],
        return_value="Value from lane (current_lane + delta)",
        example='// Wavefront reduction\\nfor (int offset = 32; offset > 0; offset >>= 1) {\\n    val += __shfl_down(val, offset);\\n}',
        cuda_equivalent="__shfl_down_sync(mask, var, delta, width)",
    ),
    "__shfl_up": IntrinsicDoc(
        name="__shfl_up",
        signature="T __shfl_up(T var, unsigned int delta, int width = warpSize)",
        description="Reads a variable from a lane with lower index (lane - delta).",
        amd_behavior="On AMD CDNA, operates on 64-thread wavefronts. Useful for prefix sums (scan operations).",
        parameters=[
            ("var", "Value to share"),
            ("delta", "Offset to subtract from current lane ID"),
            ("width", "Logical wavefront width (default: 64)"),
        ],
        return_value="Value from lane (current_lane - delta), or own value if delta > current_lane",
        cuda_equivalent="__shfl_up_sync(mask, var, delta, width)",
    ),
    "__shfl_xor": IntrinsicDoc(
        name="__shfl_xor",
        signature="T __shfl_xor(T var, int laneMask, int width = warpSize)",
        description="Reads a variable from a lane determined by XOR of current lane and mask.",
        amd_behavior="On AMD CDNA, operates on 64-thread wavefronts. Used for butterfly reductions and pair exchanges.",
        parameters=[
            ("var", "Value to share"),
            ("laneMask", "XOR mask applied to lane ID"),
            ("width", "Logical wavefront width (default: 64)"),
        ],
        return_value="Value from lane (current_lane XOR laneMask)",
        example='// Butterfly reduction\\nfor (int mask = 32; mask > 0; mask >>= 1) {\\n    val += __shfl_xor(val, mask);\\n}',
        cuda_equivalent="__shfl_xor_sync(mask, var, laneMask, width)",
    ),

    # Ballot and vote operations
    "__ballot": IntrinsicDoc(
        name="__ballot",
        signature="uint64_t __ballot(int predicate)",
        description="Returns a bitmask where bit N is set if lane N's predicate is non-zero.",
        amd_behavior="**CRITICAL**: On AMD CDNA, returns uint64_t (64 bits for 64 threads). On CUDA, __ballot_sync returns uint32_t. Code comparing to 0xFFFFFFFF will break!",
        parameters=[
            ("predicate", "Non-zero value sets the corresponding bit"),
        ],
        return_value="64-bit mask on AMD (uint64_t), 32-bit on NVIDIA (unsigned int)",
        example='uint64_t active = __ballot(threadIdx.x < limit);\\n// Check if all lanes are active:\\nif (active == 0xFFFFFFFFFFFFFFFFull) { ... }',
        cuda_equivalent="__ballot_sync(mask, predicate) - returns unsigned int",
    ),
    "__any": IntrinsicDoc(
        name="__any",
        signature="int __any(int predicate)",
        description="Returns non-zero if any lane's predicate is non-zero.",
        amd_behavior="On AMD CDNA, checks all 64 lanes in the wavefront.",
        parameters=[
            ("predicate", "Condition to test"),
        ],
        return_value="Non-zero if any lane's predicate is true",
        example='if (__any(idx < boundary)) {\\n    // At least one thread needs to do work\\n}',
        cuda_equivalent="__any_sync(mask, predicate)",
    ),
    "__all": IntrinsicDoc(
        name="__all",
        signature="int __all(int predicate)",
        description="Returns non-zero if all lanes' predicates are non-zero.",
        amd_behavior="On AMD CDNA, checks all 64 lanes in the wavefront.",
        parameters=[
            ("predicate", "Condition to test"),
        ],
        return_value="Non-zero if all lanes' predicates are true",
        example='if (__all(idx < N)) {\\n    // All threads have valid indices, no bounds check needed\\n}',
        cuda_equivalent="__all_sync(mask, predicate)",
    ),
    "__activemask": IntrinsicDoc(
        name="__activemask",
        signature="uint64_t __activemask()",
        description="Returns a mask of all currently active lanes.",
        amd_behavior="Returns uint64_t on AMD CDNA (64 bits for 64 threads). Use __popcll() to count active lanes.",
        parameters=[],
        return_value="Bitmask of active lanes (64-bit on AMD)",
        example='uint64_t active = __activemask();\\nint num_active = __popcll(active);',
        cuda_equivalent="__activemask() - but returns 32-bit on NVIDIA",
    ),

    # Bit counting
    "__popc": IntrinsicDoc(
        name="__popc",
        signature="int __popc(unsigned int x)",
        description="Counts the number of set bits (population count) in a 32-bit integer.",
        amd_behavior="Maps directly to AMD GPU VALU instruction.",
        parameters=[
            ("x", "32-bit value to count bits in"),
        ],
        return_value="Number of set bits (0-32)",
        cuda_equivalent="__popc(x)",
    ),
    "__popcll": IntrinsicDoc(
        name="__popcll",
        signature="int __popcll(unsigned long long x)",
        description="Counts the number of set bits in a 64-bit integer.",
        amd_behavior="Essential for counting active lanes from __ballot() on AMD (which returns 64-bit).",
        parameters=[
            ("x", "64-bit value to count bits in"),
        ],
        return_value="Number of set bits (0-64)",
        example='uint64_t mask = __ballot(predicate);\\nint count = __popcll(mask);  // Count how many lanes match',
        cuda_equivalent="__popcll(x)",
    ),
    "__ffs": IntrinsicDoc(
        name="__ffs",
        signature="int __ffs(int x)",
        description="Find first set bit (1-indexed from LSB). Returns 0 if no bit is set.",
        amd_behavior="Maps directly to AMD GPU instruction.",
        parameters=[
            ("x", "Value to search"),
        ],
        return_value="Position of first set bit (1-32) or 0 if none",
        cuda_equivalent="__ffs(x)",
    ),
    "__ffsll": IntrinsicDoc(
        name="__ffsll",
        signature="int __ffsll(long long x)",
        description="Find first set bit in 64-bit integer (1-indexed from LSB).",
        amd_behavior="Useful for finding first active lane from __ballot() result on AMD.",
        parameters=[
            ("x", "64-bit value to search"),
        ],
        return_value="Position of first set bit (1-64) or 0 if none",
        cuda_equivalent="__ffsll(x)",
    ),
    "__clz": IntrinsicDoc(
        name="__clz",
        signature="int __clz(int x)",
        description="Count leading zeros in a 32-bit integer.",
        amd_behavior="Maps directly to AMD GPU instruction.",
        parameters=[
            ("x", "Value to count leading zeros in"),
        ],
        return_value="Number of leading zero bits (0-32)",
        cuda_equivalent="__clz(x)",
    ),

    # Synchronization
    "__syncthreads": IntrinsicDoc(
        name="__syncthreads",
        signature="void __syncthreads()",
        description="Synchronizes all threads in a block. All threads must reach this point before any continue.",
        amd_behavior="On AMD, this is a barrier for all wavefronts in the workgroup. Wavefronts execute in lockstep, but workgroup barriers ensure all wavefronts sync.",
        parameters=[],
        return_value="void",
        example='// Load data to shared memory\\nshared_data[threadIdx.x] = global_data[idx];\\n__syncthreads();\\n// Now all threads see the complete shared data\\nuse_shared_data(shared_data);',
        cuda_equivalent="__syncthreads()",
    ),
    "__syncwarp": IntrinsicDoc(
        name="__syncwarp",
        signature="void __syncwarp(uint64_t mask = 0xFFFFFFFFFFFFFFFF)",
        description="Synchronizes threads within a wavefront.",
        amd_behavior="On AMD CDNA, wavefronts execute in lockstep (SIMD), so this is typically a no-op. However, it still provides a memory fence.",
        parameters=[
            ("mask", "Bitmask of participating lanes (64-bit on AMD)"),
        ],
        return_value="void",
        cuda_equivalent="__syncwarp(mask) - with 32-bit mask on NVIDIA",
    ),

    # Atomic operations
    "atomicAdd": IntrinsicDoc(
        name="atomicAdd",
        signature="T atomicAdd(T* address, T val)",
        description="Atomically adds val to *address and returns the old value.",
        amd_behavior="AMD GPUs have hardware atomic units. Performance depends on contention - use hierarchical atomics (warp-level reduction then global atomic) for best performance.",
        parameters=[
            ("address", "Pointer to value to update"),
            ("val", "Value to add"),
        ],
        return_value="Original value at address before the add",
        example='// Histogram update\\natomicAdd(&histogram[bin], 1);\\n\\n// Warp-level reduction then atomic (better performance)\\nfloat sum = warp_reduce(local_val);\\nif (lane_id == 0) atomicAdd(global_sum, sum);',
        cuda_equivalent="atomicAdd(address, val)",
    ),
    "atomicCAS": IntrinsicDoc(
        name="atomicCAS",
        signature="T atomicCAS(T* address, T compare, T val)",
        description="Compare-and-swap: if *address == compare, set *address = val. Returns original value.",
        amd_behavior="Fundamental atomic for implementing lock-free data structures. AMD GPUs support 32-bit and 64-bit CAS.",
        parameters=[
            ("address", "Pointer to value to update"),
            ("compare", "Expected value"),
            ("val", "New value if comparison succeeds"),
        ],
        return_value="Original value at address (compare to see if CAS succeeded)",
        example='// Lock-free update\\nunsigned int old, assumed, new_val;\\nold = *addr;\\ndo {\\n    assumed = old;\\n    new_val = compute_new(assumed);\\n    old = atomicCAS(addr, assumed, new_val);\\n} while (assumed != old);',
        cuda_equivalent="atomicCAS(address, compare, val)",
    ),
    "atomicMax": IntrinsicDoc(
        name="atomicMax",
        signature="T atomicMax(T* address, T val)",
        description="Atomically computes max(*address, val) and stores the result.",
        amd_behavior="Supported for int, unsigned int, long long, unsigned long long.",
        parameters=[
            ("address", "Pointer to value to update"),
            ("val", "Value to compare"),
        ],
        return_value="Original value at address",
        cuda_equivalent="atomicMax(address, val)",
    ),
    "atomicMin": IntrinsicDoc(
        name="atomicMin",
        signature="T atomicMin(T* address, T val)",
        description="Atomically computes min(*address, val) and stores the result.",
        amd_behavior="Supported for int, unsigned int, long long, unsigned long long.",
        parameters=[
            ("address", "Pointer to value to update"),
            ("val", "Value to compare"),
        ],
        return_value="Original value at address",
        cuda_equivalent="atomicMin(address, val)",
    ),
    "atomicExch": IntrinsicDoc(
        name="atomicExch",
        signature="T atomicExch(T* address, T val)",
        description="Atomically exchanges *address with val and returns the old value.",
        amd_behavior="Efficient atomic swap operation.",
        parameters=[
            ("address", "Pointer to value to update"),
            ("val", "New value"),
        ],
        return_value="Original value at address",
        cuda_equivalent="atomicExch(address, val)",
    ),
}

# ============================================================================
# Thread Indexing Documentation
# ============================================================================

THREAD_INDEX_DOCS: dict[str, ThreadIndexDoc] = {
    "threadIdx": ThreadIndexDoc(
        name="threadIdx",
        description="Built-in variable containing the thread's index within its block (uint3 with .x, .y, .z components).",
        amd_context="On AMD CDNA GPUs, threads are grouped into 64-thread wavefronts. threadIdx.x ranges from 0 to blockDim.x-1. The first 64 threads (threadIdx.x = 0-63) form wavefront 0, etc.",
        common_patterns=[
            "Global index: int idx = blockIdx.x * blockDim.x + threadIdx.x;",
            "Lane within wavefront: int lane = threadIdx.x % warpSize; // warpSize is 64 on AMD",
            "Wavefront within block: int warp_id = threadIdx.x / warpSize;",
            "2D indexing: int row = blockIdx.y * blockDim.y + threadIdx.y;",
        ],
    ),
    "blockIdx": ThreadIndexDoc(
        name="blockIdx",
        description="Built-in variable containing the block's index within the grid (uint3 with .x, .y, .z components).",
        amd_context="Blocks are distributed across AMD GPU Compute Units. Multiple blocks can run concurrently on a CU depending on resource usage.",
        common_patterns=[
            "Global thread index: int idx = blockIdx.x * blockDim.x + threadIdx.x;",
            "Block ID for 2D grid: int block_id = blockIdx.y * gridDim.x + blockIdx.x;",
        ],
    ),
    "blockDim": ThreadIndexDoc(
        name="blockDim",
        description="Built-in variable containing the dimensions of the block (dim3 with .x, .y, .z components).",
        amd_context="On AMD GPUs, blockDim.x * blockDim.y * blockDim.z should ideally be a multiple of 64 (wavefront size) for best occupancy.",
        common_patterns=[
            "Total threads in block: int block_size = blockDim.x * blockDim.y * blockDim.z;",
            "Linear thread ID in block: int tid = threadIdx.z * blockDim.x * blockDim.y + threadIdx.y * blockDim.x + threadIdx.x;",
        ],
    ),
    "gridDim": ThreadIndexDoc(
        name="gridDim",
        description="Built-in variable containing the dimensions of the grid (dim3 with .x, .y, .z components).",
        amd_context="Total grid dimensions. For best GPU utilization, launch enough blocks to saturate all Compute Units.",
        common_patterns=[
            "Grid-stride loop: for (int i = idx; i < N; i += gridDim.x * blockDim.x) { ... }",
            "Total blocks: int total_blocks = gridDim.x * gridDim.y * gridDim.z;",
        ],
    ),
    "warpSize": ThreadIndexDoc(
        name="warpSize",
        description="Built-in constant for the wavefront/warp size. Use this instead of hard-coding 32 or 64.",
        amd_context="On AMD CDNA GPUs (MI100, MI200, MI300), warpSize is 64. On AMD RDNA GPUs, it can be 32 or 64. Always use warpSize for portable code.",
        common_patterns=[
            "Lane ID: int lane_id = threadIdx.x % warpSize;",
            "Warp ID: int warp_id = threadIdx.x / warpSize;",
            "Number of warps in block: int num_warps = (blockDim.x + warpSize - 1) / warpSize;",
        ],
    ),
}


# ============================================================================
# HIP Docs Service
# ============================================================================

class HIPDocsService:
    """Service for looking up HIP API documentation."""

    def get_api_doc(self, name: str) -> HIPAPIDoc | None:
        """Get documentation for a HIP API function."""
        return HIP_API_DOCS.get(name)

    def get_memory_qualifier_doc(self, name: str) -> MemoryQualifierDoc | None:
        """Get documentation for a memory qualifier."""
        return MEMORY_QUALIFIER_DOCS.get(name)

    def get_intrinsic_doc(self, name: str) -> IntrinsicDoc | None:
        """Get documentation for a wavefront intrinsic."""
        return INTRINSIC_DOCS.get(name)

    def get_thread_index_doc(self, name: str) -> ThreadIndexDoc | None:
        """Get documentation for a thread indexing variable."""
        # Handle both "threadIdx" and "threadIdx.x" style
        base_name = name.split('.')[0]
        return THREAD_INDEX_DOCS.get(base_name)

    def search_apis(self, query: str) -> list[HIPAPIDoc]:
        """Search for APIs matching a query."""
        query_lower = query.lower()
        results = []
        for name, doc in HIP_API_DOCS.items():
            if query_lower in name.lower() or query_lower in doc.description.lower():
                results.append(doc)
        return results

    def get_all_api_names(self) -> list[str]:
        """Get all known API function names."""
        return list(HIP_API_DOCS.keys())

    def get_all_intrinsic_names(self) -> list[str]:
        """Get all known intrinsic names."""
        return list(INTRINSIC_DOCS.keys())


def create_hip_docs_service() -> HIPDocsService:
    """Create a HIP documentation service instance."""
    return HIPDocsService()
