/**
 * Example HIP kernel file for testing wafer-lsp HIP support.
 * This file demonstrates various HIP constructs that the LSP should recognize.
 */

#include <hip/hip_runtime.h>
#include <stdio.h>

// Constants
#define BLOCK_SIZE 256
#define WARP_SIZE 32  // HIP001: Should use warpSize instead of 32

/**
 * Helper device function for reduction.
 * Reduces values within a warp using shuffle operations.
 */
__device__ __forceinline__ float warp_reduce_sum(float val) {
    // HIP002: Using hardcoded 32 as width - should use warpSize
    for (int offset = 16; offset > 0; offset >>= 1) {
        val += __shfl_down(val, offset, 32);  // Should be warpSize or omit width
    }
    return val;
}

/**
 * Another device helper demonstrating ballot operations.
 */
__device__ int count_active_threads(int predicate) {
    // HIP003: __ballot returns uint64_t on AMD, not uint32_t
    uint64_t mask = __ballot(predicate);
    return __popcll(mask);  // Use 64-bit popcount
}

// Shared memory for tile-based operations
__shared__ float shared_tile[32][33];  // Padded to avoid bank conflicts

/**
 * Simple vector addition kernel.
 * Demonstrates basic HIP kernel structure.
 */
__global__ void vector_add(
    const float* __restrict__ a,
    const float* __restrict__ b,
    float* __restrict__ c,
    int n
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Grid-stride loop for handling large arrays
    for (int i = idx; i < n; i += gridDim.x * blockDim.x) {
        c[i] = a[i] + b[i];
    }
}

/**
 * Matrix multiplication kernel with shared memory tiling.
 * Shows more complex HIP patterns.
 */
__global__ __launch_bounds__(256, 4)
void matmul_tiled(
    const float* __restrict__ A,
    const float* __restrict__ B,
    float* __restrict__ C,
    int M, int N, int K
) {
    // Thread indices
    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int bx = blockIdx.x;
    int by = blockIdx.y;
    
    // HIP001: Incorrect lane calculation - uses 32 instead of warpSize
    int lane = threadIdx.x % 32;  // Should be: threadIdx.x % warpSize
    int warp_id = threadIdx.x / 32;  // Should be: threadIdx.x / warpSize
    
    // Shared memory tiles
    __shared__ float As[16][16];
    __shared__ float Bs[16][16];
    
    float sum = 0.0f;
    
    // Tiled computation
    for (int t = 0; t < (K + 15) / 16; ++t) {
        // Load tiles to shared memory
        int aRow = by * 16 + ty;
        int aCol = t * 16 + tx;
        int bRow = t * 16 + ty;
        int bCol = bx * 16 + tx;
        
        As[ty][tx] = (aRow < M && aCol < K) ? A[aRow * K + aCol] : 0.0f;
        Bs[ty][tx] = (bRow < K && bCol < N) ? B[bRow * N + bCol] : 0.0f;
        
        __syncthreads();
        
        // Compute partial sum
        #pragma unroll
        for (int k = 0; k < 16; ++k) {
            sum += As[ty][k] * Bs[k][tx];
        }
        
        __syncthreads();
    }
    
    // Write result
    int row = by * 16 + ty;
    int col = bx * 16 + tx;
    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}

/**
 * Reduction kernel demonstrating wavefront operations.
 * Shows patterns that need AMD wavefront awareness.
 */
__global__ void reduce_sum(
    const float* __restrict__ input,
    float* __restrict__ output,
    int n
) {
    extern __shared__ float sdata[];  // Dynamic shared memory
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Load input to shared memory
    sdata[tid] = (idx < n) ? input[idx] : 0.0f;
    __syncthreads();
    
    // Block-level reduction
    for (int s = blockDim.x / 2; s > 32; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    
    // HIP001: Warp-level reduction with incorrect size
    // This assumes 32-thread warps, but AMD has 64-thread wavefronts
    if (tid < 32) {
        volatile float* smem = sdata;
        // These unrolled steps assume warp size of 32
        if (blockDim.x >= 64) smem[tid] += smem[tid + 32];
        if (blockDim.x >= 32) smem[tid] += smem[tid + 16];
        smem[tid] += smem[tid + 8];
        smem[tid] += smem[tid + 4];
        smem[tid] += smem[tid + 2];
        smem[tid] += smem[tid + 1];
    }
    
    // HIP003: Ballot comparison with 32-bit mask
    if (__ballot(tid == 0) == 0xFFFFFFFF) {  // Should be 0xFFFFFFFFFFFFFFFFull
        // This is wrong - AMD ballot returns 64-bit
    }
    
    if (tid == 0) {
        output[blockIdx.x] = sdata[0];
    }
}

/**
 * Correct AMD-aware reduction using warpSize.
 * This demonstrates the portable way to write wavefront code.
 */
__global__ void reduce_sum_portable(
    const float* __restrict__ input,
    float* __restrict__ output,
    int n
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < n) ? input[idx] : 0.0f;
    __syncthreads();
    
    // Correct: Use warpSize for portable code
    for (int s = blockDim.x / 2; s > warpSize; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    
    // Wavefront-level reduction using warpSize
    if (tid < warpSize) {
        // Use shuffle for wavefront reduction
        float val = sdata[tid];
        for (int offset = warpSize / 2; offset > 0; offset >>= 1) {
            val += __shfl_down(val, offset);  // Correct: no explicit width
        }
        if (tid == 0) {
            output[blockIdx.x] = val;
        }
    }
}

// Host code
int main() {
    const int N = 1024;
    float *h_a, *h_b, *h_c;
    float *d_a, *d_b, *d_c;
    
    // Allocate host memory
    h_a = (float*)malloc(N * sizeof(float));
    h_b = (float*)malloc(N * sizeof(float));
    h_c = (float*)malloc(N * sizeof(float));
    
    // Initialize
    for (int i = 0; i < N; i++) {
        h_a[i] = 1.0f;
        h_b[i] = 2.0f;
    }
    
    // Allocate device memory
    hipMalloc(&d_a, N * sizeof(float));
    hipMalloc(&d_b, N * sizeof(float));
    hipMalloc(&d_c, N * sizeof(float));
    
    // Copy to device
    hipMemcpy(d_a, h_a, N * sizeof(float), hipMemcpyHostToDevice);
    hipMemcpy(d_b, h_b, N * sizeof(float), hipMemcpyHostToDevice);
    
    // Launch kernel
    int blockSize = 256;
    int gridSize = (N + blockSize - 1) / blockSize;
    
    vector_add<<<gridSize, blockSize>>>(d_a, d_b, d_c, N);
    
    // Alternative launch syntax
    hipLaunchKernelGGL(vector_add, dim3(gridSize), dim3(blockSize), 0, 0, d_a, d_b, d_c, N);
    
    // Synchronize
    hipDeviceSynchronize();
    
    // Check for errors
    hipError_t err = hipGetLastError();
    if (err != hipSuccess) {
        printf("Error: %s\n", hipGetErrorString(err));
        return 1;
    }
    
    // Copy result back
    hipMemcpy(h_c, d_c, N * sizeof(float), hipMemcpyDeviceToHost);
    
    // Verify
    for (int i = 0; i < N; i++) {
        if (h_c[i] != 3.0f) {
            printf("Verification failed at index %d: %f != 3.0\n", i, h_c[i]);
            return 1;
        }
    }
    printf("Verification passed!\n");
    
    // Cleanup
    hipFree(d_a);
    hipFree(d_b);
    hipFree(d_c);
    free(h_a);
    free(h_b);
    free(h_c);
    
    return 0;
}
