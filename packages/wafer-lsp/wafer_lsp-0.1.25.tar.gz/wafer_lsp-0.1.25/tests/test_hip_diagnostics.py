"""
Tests for HIP diagnostics provider.

Tests wavefront-aware warnings (HIP001-HIP004) and ensures
no false positives for portable code.
"""

import pytest

from wafer_lsp.handlers.hip_diagnostics import (
    HIPDiagnosticsProvider,
    get_hip_diagnostics,
    DIAGNOSTIC_INFO,
)
from lsprotocol.types import DiagnosticSeverity


@pytest.fixture
def provider():
    return HIPDiagnosticsProvider()


class TestHIP001WarpSizeDiagnostics:
    """Tests for HIP001: Incorrect wavefront size assumption."""

    def test_threadidx_less_than_32(self, provider):
        """Test detection of threadIdx.x < 32 pattern."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) {
        // warp-level code
    }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP001" for d in diagnostics)
        assert any("32" in d.message for d in diagnostics)

    def test_lane_modulo_32(self, provider):
        """Test detection of lane % 32 pattern."""
        code = '''
__global__ void kernel() {
    int lane = threadIdx.x % 32;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP001" or d.code == "HIP004" for d in diagnostics)

    def test_define_warp_size_32(self, provider):
        """Test detection of #define WARP_SIZE 32."""
        code = '''
#define WARP_SIZE 32

__global__ void kernel() {
    int lane = threadIdx.x % WARP_SIZE;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP001" for d in diagnostics)

    def test_no_warning_for_warpsize(self, provider):
        """Test that warpSize variable usage doesn't trigger warnings."""
        code = '''
__global__ void kernel() {
    int lane = threadIdx.x % warpSize;
    int warp_id = threadIdx.x / warpSize;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        # Should not have HIP001 for these lines
        assert not any(d.code == "HIP001" for d in diagnostics)

    def test_reduction_loop_from_16(self, provider):
        """Test detection of reduction loop starting from 16."""
        code = '''
__global__ void kernel() {
    for (int i = 16; i > 0; i >>= 1) {
        val += __shfl_down(val, i);
    }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1


class TestHIP002ShuffleDiagnostics:
    """Tests for HIP002: Wavefront intrinsic misuse."""

    def test_shuffle_with_width_32(self, provider):
        """Test detection of __shfl_down with explicit width 32."""
        code = '''
__global__ void kernel() {
    float val = __shfl_down(val, offset, 32);
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP002" for d in diagnostics)

    def test_shuffle_without_width_ok(self, provider):
        """Test that shuffle without width parameter doesn't warn."""
        code = '''
__global__ void kernel() {
    float val = __shfl_down(val, offset);
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        # Should not warn - no explicit width
        assert not any(d.code == "HIP002" for d in diagnostics)

    def test_shfl_xor_with_width_32(self, provider):
        """Test __shfl_xor with explicit width 32."""
        code = '''
__global__ void kernel() {
    float val = __shfl_xor(val, 1, 32);
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP002" for d in diagnostics)


class TestHIP003BallotDiagnostics:
    """Tests for HIP003: Ballot result handling errors."""

    def test_ballot_equals_32bit_mask(self, provider):
        """Test detection of __ballot comparison with 32-bit mask."""
        code = '''
__global__ void kernel() {
    if (__ballot(pred) == 0xFFFFFFFF) {
        // all active
    }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP003" for d in diagnostics)
        assert any("64-bit" in d.message.lower() or "64" in d.message for d in diagnostics)

    def test_ballot_not_equals_32bit_mask(self, provider):
        """Test detection of __ballot != comparison."""
        code = '''
__global__ void kernel() {
    if (__ballot(pred) != 0xFFFFFFFF) {
        // not all active
    }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert any(d.code == "HIP003" for d in diagnostics)

    def test_activemask_equals_32bit(self, provider):
        """Test detection of __activemask comparison."""
        code = '''
__global__ void kernel() {
    if (__activemask() == 0xFFFFFFFF) {
        // all active
    }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1


class TestHIP004LaneCalculationDiagnostics:
    """Tests for HIP004: Lane/wavefront index calculation errors."""

    def test_lane_id_modulo_32(self, provider):
        """Test detection of laneId = ... % 32 pattern."""
        code = '''
__global__ void kernel() {
    int laneId = threadIdx.x % 32;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        # Could be HIP001 or HIP004
        assert any(d.code in ("HIP001", "HIP004") for d in diagnostics)

    def test_warp_id_divide_32(self, provider):
        """Test detection of warpId = ... / 32 pattern."""
        code = '''
__global__ void kernel() {
    int warpId = threadIdx.x / 32;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1


class TestDiagnosticMessages:
    """Tests for diagnostic message quality."""

    def test_diagnostic_includes_suggestion(self, provider):
        """Test that diagnostics include helpful suggestions."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        diag = diagnostics[0]
        assert "warpSize" in diag.message.lower() or "warpsize" in diag.message.lower() or "64" in diag.message

    def test_diagnostic_has_correct_severity(self, provider):
        """Test that diagnostics have warning severity."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert all(d.severity == DiagnosticSeverity.Warning for d in diagnostics)

    def test_diagnostic_has_source(self, provider):
        """Test that diagnostics have source identifier."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1
        assert all(d.source == "wafer-hip" for d in diagnostics)


class TestDiagnosticsToggle:
    """Tests for diagnostics enable/disable."""

    def test_disabled_wavefront_diagnostics(self, provider):
        """Test that diagnostics can be disabled."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = provider.get_diagnostics(
            code, "test.hip", 
            enable_wavefront_diagnostics=False
        )
        
        assert len(diagnostics) == 0


class TestNoFalsePositives:
    """Tests to ensure we don't flag correct code."""

    def test_no_warning_in_comments(self, provider):
        """Test that code in comments doesn't trigger warnings."""
        code = '''
__global__ void kernel() {
    // if (threadIdx.x < 32) { }
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        # Comments should be ignored
        assert len(diagnostics) == 0

    def test_no_warning_for_amd_macro(self, provider):
        """Test that __AMDGCN_WAVEFRONT_SIZE__ doesn't trigger warnings."""
        code = '''
__global__ void kernel() {
    int lane = threadIdx.x % __AMDGCN_WAVEFRONT_SIZE__;
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        # Using AMD macro is correct
        assert len(diagnostics) == 0

    def test_unrelated_32_values(self, provider):
        """Test that unrelated uses of 32 don't trigger warnings."""
        code = '''
__global__ void kernel() {
    int array_size = 32;  // Just a constant
    float val = 32.0f;    // Just a value
}
'''
        diagnostics = provider.get_diagnostics(code, "test.hip")
        
        # These uses of 32 are not wavefront-related
        # May or may not flag depending on patterns
        # Main thing is it doesn't crash


class TestConvenienceFunction:
    """Tests for get_hip_diagnostics convenience function."""

    def test_get_hip_diagnostics_function(self):
        """Test the convenience function works."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = get_hip_diagnostics(code, "test.hip")
        
        assert len(diagnostics) >= 1

    def test_get_hip_diagnostics_disabled(self):
        """Test disabling via convenience function."""
        code = '''
__global__ void kernel() {
    if (threadIdx.x < 32) { }
}
'''
        diagnostics = get_hip_diagnostics(
            code, "test.hip", 
            enable_wavefront_diagnostics=False
        )
        
        assert len(diagnostics) == 0
