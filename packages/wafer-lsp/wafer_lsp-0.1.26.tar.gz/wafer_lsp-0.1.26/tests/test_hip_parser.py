"""
Tests for the HIP parser.

Tests kernel extraction, device function extraction, shared memory detection,
launch site detection, and wavefront pattern detection.
"""

import pytest

from wafer_lsp.parsers.hip_parser import (
    HIPParser,
    HIPKernel,
    HIPDeviceFunction,
    SharedMemoryAllocation,
    KernelLaunchSite,
    WavefrontPattern,
    is_hip_file,
)


@pytest.fixture
def parser():
    return HIPParser()


class TestHIPParserKernelExtraction:
    """Tests for kernel extraction from HIP code."""

    def test_simple_kernel(self, parser):
        """Test extracting a simple __global__ kernel."""
        code = '''
__global__ void vector_add(float* a, float* b, float* c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) c[idx] = a[idx] + b[idx];
}
'''
        result = parser.parse_file(code)
        kernels = result["kernels"]
        
        assert len(kernels) == 1
        assert kernels[0].name == "vector_add"
        assert "a" in kernels[0].parameters
        assert "b" in kernels[0].parameters
        assert "c" in kernels[0].parameters
        assert "n" in kernels[0].parameters

    def test_kernel_with_launch_bounds(self, parser):
        """Test kernel with __launch_bounds__ attribute."""
        code = '''
__global__ __launch_bounds__(256, 4)
void matmul_kernel(float* A, float* B, float* C) {
    // kernel body
}
'''
        result = parser.parse_file(code)
        kernels = result["kernels"]
        
        assert len(kernels) == 1
        assert kernels[0].name == "matmul_kernel"
        assert len(kernels[0].attributes) == 1
        assert "__launch_bounds__(256, 4)" in kernels[0].attributes[0]

    def test_templated_kernel(self, parser):
        """Test templated kernel extraction."""
        code = '''
template <typename T, int BLOCK_SIZE>
__global__ void templated_kernel(T* data, int n) {
    // kernel body
}
'''
        result = parser.parse_file(code)
        kernels = result["kernels"]
        
        assert len(kernels) == 1
        assert kernels[0].name == "templated_kernel"

    def test_multiple_kernels(self, parser):
        """Test extracting multiple kernels from one file."""
        code = '''
__global__ void kernel1(float* a) { }
__global__ void kernel2(float* b) { }
__global__ void kernel3(float* c, int n) { }
'''
        result = parser.parse_file(code)
        kernels = result["kernels"]
        
        assert len(kernels) == 3
        names = [k.name for k in kernels]
        assert "kernel1" in names
        assert "kernel2" in names
        assert "kernel3" in names

    def test_kernel_with_docstring(self, parser):
        """Test kernel docstring extraction."""
        code = '''
/**
 * Performs element-wise addition of two arrays.
 */
__global__ void add_kernel(float* a, float* b, float* c) {
    // body
}
'''
        result = parser.parse_file(code)
        kernels = result["kernels"]
        
        assert len(kernels) == 1
        assert kernels[0].docstring is not None
        assert "element-wise addition" in kernels[0].docstring


class TestHIPParserDeviceFunctions:
    """Tests for device function extraction."""

    def test_simple_device_function(self, parser):
        """Test extracting a __device__ function."""
        code = '''
__device__ float helper_func(float x, float y) {
    return x + y;
}
'''
        result = parser.parse_file(code)
        device_funcs = result["device_functions"]
        
        assert len(device_funcs) == 1
        assert device_funcs[0].name == "helper_func"
        assert device_funcs[0].return_type == "float"
        assert "x" in device_funcs[0].parameters
        assert "y" in device_funcs[0].parameters

    def test_forceinline_device_function(self, parser):
        """Test __forceinline__ device function."""
        code = '''
__device__ __forceinline__ float fast_helper(float x) {
    return x * 2.0f;
}
'''
        result = parser.parse_file(code)
        device_funcs = result["device_functions"]
        
        assert len(device_funcs) == 1
        assert device_funcs[0].is_inline is True

    def test_device_function_not_from_global(self, parser):
        """Ensure __device__ in __global__ __device__ is not double-counted."""
        code = '''
__global__ __device__ void hybrid_func(float* data) {
    // body
}
'''
        result = parser.parse_file(code)
        
        # Should be treated as a kernel, not a device function
        assert len(result["kernels"]) == 1
        assert len(result["device_functions"]) == 0


class TestHIPParserSharedMemory:
    """Tests for shared memory detection."""

    def test_static_shared_memory(self, parser):
        """Test static __shared__ memory detection."""
        code = '''
__global__ void kernel() {
    __shared__ float shared_data[256];
}
'''
        result = parser.parse_file(code)
        shared = result["shared_memory"]
        
        assert len(shared) == 1
        assert shared[0].name == "shared_data"
        assert shared[0].type_str == "float"
        assert "[256]" in shared[0].array_size or shared[0].array_size == "256"
        assert shared[0].size_bytes == 256 * 4  # float is 4 bytes

    def test_dynamic_shared_memory(self, parser):
        """Test extern __shared__ (dynamic) memory detection."""
        code = '''
__global__ void kernel() {
    extern __shared__ float dynamic_data[];
}
'''
        result = parser.parse_file(code)
        shared = result["shared_memory"]
        
        assert len(shared) == 1
        assert shared[0].name == "dynamic_data"
        assert shared[0].is_dynamic is True

    def test_2d_shared_memory(self, parser):
        """Test 2D shared memory array."""
        code = '''
__global__ void kernel() {
    __shared__ float tile[16][16];
}
'''
        result = parser.parse_file(code)
        shared = result["shared_memory"]
        
        # Note: our simple regex may only capture first dimension
        assert len(shared) >= 1
        assert shared[0].name == "tile"


class TestHIPParserLaunchSites:
    """Tests for kernel launch site detection."""

    def test_triple_chevron_launch(self, parser):
        """Test <<<>>> launch syntax detection."""
        code = '''
int main() {
    kernel<<<gridSize, blockSize>>>(data, n);
}
'''
        result = parser.parse_file(code)
        launches = result["launch_sites"]
        
        assert len(launches) == 1
        assert launches[0].kernel_name == "kernel"
        assert launches[0].grid_dim == "gridSize"
        assert launches[0].block_dim == "blockSize"
        assert launches[0].is_hip_launch_kernel_ggl is False

    def test_launch_with_shared_and_stream(self, parser):
        """Test launch with shared memory and stream parameters."""
        code = '''
int main() {
    kernel<<<grid, block, sharedMem, stream>>>(data, n);
}
'''
        result = parser.parse_file(code)
        launches = result["launch_sites"]
        
        assert len(launches) == 1
        assert launches[0].shared_mem_bytes == "sharedMem"
        assert launches[0].stream == "stream"

    def test_hip_launch_kernel_ggl(self, parser):
        """Test hipLaunchKernelGGL detection."""
        code = '''
int main() {
    hipLaunchKernelGGL(myKernel, dim3(grid), dim3(block), 0, stream, arg1, arg2);
}
'''
        result = parser.parse_file(code)
        launches = result["launch_sites"]
        
        assert len(launches) == 1
        assert launches[0].kernel_name == "myKernel"
        assert launches[0].is_hip_launch_kernel_ggl is True


class TestHIPParserWavefrontPatterns:
    """Tests for wavefront-sensitive pattern detection."""

    def test_warp_size_32_pattern(self, parser):
        """Test detection of hard-coded warp size 32."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) {
        // warp-level code
    }
}
'''
        result = parser.parse_file(code)
        patterns = result["wavefront_patterns"]
        
        assert len(patterns) >= 1
        assert any(p.pattern_type == "warp_size_32" for p in patterns)
        assert any(p.problematic_value == "32" for p in patterns)

    def test_lane_calculation_pattern(self, parser):
        """Test detection of incorrect lane calculation."""
        code = '''
__global__ void kernel() {
    int lane = threadIdx.x % 32;
    int warp_id = threadIdx.x / 32;
}
'''
        result = parser.parse_file(code)
        patterns = result["wavefront_patterns"]
        
        # Should detect both patterns
        assert len(patterns) >= 2

    def test_ballot_32bit_pattern(self, parser):
        """Test detection of 32-bit ballot comparison."""
        code = '''
__global__ void kernel() {
    if (__ballot(threadIdx.x == 0) == 0xFFFFFFFF) {
        // all threads active
    }
}
'''
        result = parser.parse_file(code)
        patterns = result["wavefront_patterns"]
        
        assert len(patterns) >= 1
        assert any(p.pattern_type == "ballot_32bit" for p in patterns)
        assert any(p.problematic_value == "0xFFFFFFFF" for p in patterns)

    def test_shuffle_width_pattern(self, parser):
        """Test detection of shuffle with explicit width 32."""
        code = '''
__global__ void kernel() {
    float val = __shfl_down(val, offset, 32);
}
'''
        result = parser.parse_file(code)
        patterns = result["wavefront_patterns"]
        
        assert len(patterns) >= 1
        assert any(p.pattern_type == "shuffle_mask" for p in patterns)

    def test_no_warning_for_warpsize(self, parser):
        """Test that using warpSize doesn't trigger warnings."""
        code = '''
__global__ void kernel() {
    int lane = threadIdx.x % warpSize;  // Correct!
    int warp_id = threadIdx.x / warpSize;  // Correct!
}
'''
        result = parser.parse_file(code)
        patterns = result["wavefront_patterns"]
        
        # Should not detect any patterns - using warpSize is correct
        assert len(patterns) == 0


class TestIsHIPFile:
    """Tests for HIP file content detection."""

    def test_hip_runtime_include(self):
        """Test detection via hip_runtime.h include."""
        code = '#include <hip/hip_runtime.h>\n__global__ void kernel() {}'
        assert is_hip_file(code) is True

    def test_hip_malloc(self):
        """Test detection via hipMalloc usage."""
        code = 'void* ptr; hipMalloc(&ptr, 1024);'
        assert is_hip_file(code) is True

    def test_hip_launch_kernel_ggl(self):
        """Test detection via hipLaunchKernelGGL."""
        code = 'hipLaunchKernelGGL(kernel, grid, block, 0, 0, args);'
        assert is_hip_file(code) is True

    def test_not_hip_file(self):
        """Test that regular CUDA code is not detected as HIP."""
        code = '#include <cuda_runtime.h>\n__global__ void kernel() {}'
        assert is_hip_file(code) is False


class TestHIPParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse_file("")
        assert result["kernels"] == []
        assert result["device_functions"] == []
        assert result["shared_memory"] == []
        assert result["launch_sites"] == []
        assert result["wavefront_patterns"] == []

    def test_incomplete_kernel(self, parser):
        """Test parsing incomplete kernel (during editing)."""
        code = '''
__global__ void incomplete_kernel(float* data
'''
        # Should not crash
        result = parser.parse_file(code)
        # May or may not extract partial info

    def test_nested_templates(self, parser):
        """Test handling of nested template parameters."""
        code = '''
template <typename T, int N>
__global__ void kernel(cute::Tensor<T, cute::Layout<Shape<N, N>>> tensor) {
}
'''
        result = parser.parse_file(code)
        # Should not crash on complex templates
        assert len(result["kernels"]) == 1
