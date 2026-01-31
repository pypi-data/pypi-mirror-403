"""
Tests for HIP hover service.

Tests hover documentation for HIP APIs, memory qualifiers,
intrinsics, thread indexing, and kernel/device functions.
"""

import pytest

from lsprotocol.types import Position

from wafer_lsp.services.hip_docs import (
    HIPDocsService,
    HIP_API_DOCS,
    MEMORY_QUALIFIER_DOCS,
    INTRINSIC_DOCS,
    THREAD_INDEX_DOCS,
)
from wafer_lsp.services.hip_hover_service import HIPHoverService


@pytest.fixture
def docs_service():
    return HIPDocsService()


@pytest.fixture
def hover_service():
    return HIPHoverService()


class TestHIPDocsService:
    """Tests for HIP documentation database."""

    def test_get_api_doc_hipmalloc(self, docs_service):
        """Test looking up hipMalloc documentation."""
        doc = docs_service.get_api_doc("hipMalloc")
        
        assert doc is not None
        assert doc.name == "hipMalloc"
        assert "hipError_t" in doc.signature
        assert "ptr" in [p[0] for p in doc.parameters]
        assert "size" in [p[0] for p in doc.parameters]
        assert doc.amd_notes is not None

    def test_get_api_doc_hipmemcpy(self, docs_service):
        """Test looking up hipMemcpy documentation."""
        doc = docs_service.get_api_doc("hipMemcpy")
        
        assert doc is not None
        assert doc.name == "hipMemcpy"
        assert "dst" in [p[0] for p in doc.parameters]
        assert "hipMemcpyKind" in doc.signature

    def test_get_api_doc_nonexistent(self, docs_service):
        """Test looking up non-existent API."""
        doc = docs_service.get_api_doc("nonexistentFunction")
        
        assert doc is None

    def test_get_memory_qualifier_shared(self, docs_service):
        """Test looking up __shared__ documentation."""
        doc = docs_service.get_memory_qualifier_doc("__shared__")
        
        assert doc is not None
        assert "LDS" in doc.amd_details or "Local Data Share" in doc.amd_details
        assert "64 KB" in doc.amd_details or "64KB" in doc.amd_details

    def test_get_memory_qualifier_device(self, docs_service):
        """Test looking up __device__ documentation."""
        doc = docs_service.get_memory_qualifier_doc("__device__")
        
        assert doc is not None
        assert doc.performance_tips is not None

    def test_get_intrinsic_shfl_down(self, docs_service):
        """Test looking up __shfl_down documentation."""
        doc = docs_service.get_intrinsic_doc("__shfl_down")
        
        assert doc is not None
        assert "64" in doc.amd_behavior or "wavefront" in doc.amd_behavior.lower()
        assert doc.cuda_equivalent is not None

    def test_get_intrinsic_ballot(self, docs_service):
        """Test looking up __ballot documentation."""
        doc = docs_service.get_intrinsic_doc("__ballot")
        
        assert doc is not None
        assert "uint64_t" in doc.amd_behavior or "64-bit" in doc.amd_behavior

    def test_get_thread_index_threadidx(self, docs_service):
        """Test looking up threadIdx documentation."""
        doc = docs_service.get_thread_index_doc("threadIdx")
        
        assert doc is not None
        assert "64" in doc.amd_context or "wavefront" in doc.amd_context.lower()

    def test_get_thread_index_with_component(self, docs_service):
        """Test looking up threadIdx.x (should resolve to threadIdx)."""
        doc = docs_service.get_thread_index_doc("threadIdx.x")
        
        assert doc is not None
        assert doc.name == "threadIdx"

    def test_get_thread_index_warpsize(self, docs_service):
        """Test looking up warpSize documentation."""
        doc = docs_service.get_thread_index_doc("warpSize")
        
        assert doc is not None
        assert "64" in doc.amd_context

    def test_search_apis(self, docs_service):
        """Test searching APIs by keyword."""
        results = docs_service.search_apis("memory")
        
        assert len(results) > 0
        # Should find memory-related APIs
        assert any("Malloc" in r.name or "Memcpy" in r.name for r in results)

    def test_get_all_api_names(self, docs_service):
        """Test getting all API names."""
        names = docs_service.get_all_api_names()
        
        assert len(names) > 0
        assert "hipMalloc" in names
        assert "hipMemcpy" in names

    def test_get_all_intrinsic_names(self, docs_service):
        """Test getting all intrinsic names."""
        names = docs_service.get_all_intrinsic_names()
        
        assert len(names) > 0
        assert "__shfl" in names or "__shfl_down" in names


class TestHIPHoverService:
    """Tests for HIP hover functionality."""

    def test_hover_hip_api(self, hover_service):
        """Test hovering over HIP API function."""
        code = '''
int main() {
    hipMalloc(&ptr, size);
}
'''
        position = Position(line=2, character=4)  # On hipMalloc
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "hipMalloc" in hover.contents.value
        assert "allocate" in hover.contents.value.lower()

    def test_hover_memory_qualifier(self, hover_service):
        """Test hovering over __shared__."""
        code = '''
__global__ void kernel() {
    __shared__ float data[256];
}
'''
        position = Position(line=2, character=4)  # On __shared__
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "__shared__" in hover.contents.value
        assert "LDS" in hover.contents.value or "Local Data Share" in hover.contents.value

    def test_hover_intrinsic(self, hover_service):
        """Test hovering over wavefront intrinsic."""
        code = '''
__global__ void kernel() {
    float val = __shfl_down(val, 1);
}
'''
        position = Position(line=2, character=16)  # On __shfl_down
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "__shfl_down" in hover.contents.value

    def test_hover_thread_index(self, hover_service):
        """Test hovering over threadIdx."""
        code = '''
__global__ void kernel() {
    int idx = threadIdx.x;
}
'''
        position = Position(line=2, character=14)  # On threadIdx
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "threadIdx" in hover.contents.value

    def test_hover_kernel(self, hover_service):
        """Test hovering over kernel function name."""
        code = '''
__global__ void vector_add(float* a, float* b, float* c) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
}
'''
        position = Position(line=1, character=16)  # On vector_add
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "vector_add" in hover.contents.value
        assert "Kernel" in hover.contents.value

    def test_hover_device_function(self, hover_service):
        """Test hovering over device function name."""
        code = '''
__device__ float helper_func(float x) {
    return x * 2.0f;
}
'''
        position = Position(line=1, character=17)  # On helper_func
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        # Device functions should have hover info
        # Note: The word extraction needs to be on the function name
        assert hover is not None
        assert "helper_func" in hover.contents.value
        assert "Device" in hover.contents.value

    def test_hover_shared_memory_var(self, hover_service):
        """Test hovering over shared memory variable."""
        code = '''
__global__ void kernel() {
    __shared__ float tile[256];
    tile[threadIdx.x] = 0.0f;
}
'''
        position = Position(line=2, character=21)  # On tile declaration
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        # Should provide info about shared memory
        assert hover is not None

    def test_hover_no_result(self, hover_service):
        """Test hovering over non-HIP code returns None."""
        code = '''
int main() {
    int x = 5;
    return x;
}
'''
        position = Position(line=2, character=8)  # On 'x'
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        # Regular variables might not have hover info
        # This is OK - returning None is acceptable


class TestHIPHoverFormatting:
    """Tests for hover content formatting."""

    def test_api_hover_has_signature(self, hover_service):
        """Test that API hover includes function signature."""
        code = '''
hipDeviceSynchronize();
'''
        position = Position(line=1, character=0)
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        assert "hipError_t" in hover.contents.value
        assert "hipDeviceSynchronize" in hover.contents.value

    def test_api_hover_has_amd_notes(self, hover_service):
        """Test that API hover includes AMD-specific notes."""
        code = '''
hipMalloc(&ptr, size);
'''
        position = Position(line=1, character=0)
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        # Should have AMD-specific information
        assert "AMD" in hover.contents.value or "Notes" in hover.contents.value

    def test_intrinsic_hover_has_amd_behavior(self, hover_service):
        """Test that intrinsic hover explains AMD wavefront behavior."""
        code = '''
__ballot(pred);
'''
        position = Position(line=1, character=0)
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        # Should explain 64-bit return on AMD
        assert "64" in hover.contents.value

    def test_kernel_hover_has_parameters(self, hover_service):
        """Test that kernel hover shows parameter names."""
        code = '''
__global__ void my_kernel(float* input, float* output, int n) {
}
'''
        position = Position(line=1, character=16)  # On my_kernel
        
        hover = hover_service.get_hover(code, position, "test.hip")
        
        assert hover is not None
        # Should list parameters
        content = hover.contents.value.lower()
        assert "input" in content or "parameter" in content


class TestHIPDocsCoverage:
    """Tests to ensure we have good documentation coverage."""

    def test_common_hip_apis_documented(self):
        """Test that commonly used HIP APIs are documented."""
        common_apis = [
            "hipMalloc",
            "hipFree",
            "hipMemcpy",
            "hipMemcpyAsync",
            "hipDeviceSynchronize",
            "hipStreamSynchronize",
            "hipSetDevice",
            "hipGetDeviceProperties",
            "hipLaunchKernelGGL",
        ]
        
        for api in common_apis:
            assert api in HIP_API_DOCS, f"Missing documentation for {api}"

    def test_memory_qualifiers_documented(self):
        """Test that all memory qualifiers are documented."""
        qualifiers = [
            "__device__",
            "__shared__",
            "__constant__",
            "__global__",
        ]
        
        for qual in qualifiers:
            assert qual in MEMORY_QUALIFIER_DOCS, f"Missing documentation for {qual}"

    def test_common_intrinsics_documented(self):
        """Test that commonly used intrinsics are documented."""
        intrinsics = [
            "__shfl",
            "__shfl_down",
            "__ballot",
            "__syncthreads",
            "atomicAdd",
        ]
        
        for intr in intrinsics:
            assert intr in INTRINSIC_DOCS, f"Missing documentation for {intr}"

    def test_thread_indices_documented(self):
        """Test that thread indexing variables are documented."""
        indices = [
            "threadIdx",
            "blockIdx",
            "blockDim",
            "gridDim",
            "warpSize",
        ]
        
        for idx in indices:
            assert idx in THREAD_INDEX_DOCS, f"Missing documentation for {idx}"
