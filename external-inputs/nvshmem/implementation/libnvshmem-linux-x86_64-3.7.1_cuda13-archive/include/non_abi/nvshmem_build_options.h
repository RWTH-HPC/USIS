/*
 * Copyright (c) 2018-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

/* #undef NVSHMEM_COMPLEX_SUPPORT */
/* #undef NVSHMEM_DEBUG */
/* #undef NVSHMEM_DEVEL */
/* #undef NVSHMEM_TRACE */
/* #undef NVSHMEM_DEFAULT_PMI2 */
/* #undef NVSHMEM_DEFAULT_PMIX */
/* #undef NVSHMEM_DEFAULT_UCX */
/* #undef NVSHMEM_GPU_COLL_USE_LDST */
#define NVSHMEM_IBDEVX_SUPPORT
#define NVSHMEM_IBRC_SUPPORT
#define NVSHMEM_LIBFABRIC_SUPPORT
#define NVSHMEM_MPI_SUPPORT
#define NVSHMEM_NVTX
#define NVSHMEM_PMIX_SUPPORT
#define NVSHMEM_SHMEM_SUPPORT
/* #undef NVSHMEM_TIMEOUT_DEVICE_POLLING */
#define NVSHMEM_UCX_SUPPORT
/* #undef NVSHMEM_USE_DLMALLOC */
#define NVSHMEM_USE_NCCL
#define NVSHMEM_USE_GDRCOPY
#define NVSHMEM_USE_MLX5DV
/* #undef NVSHMEM_ENABLE_CFT_HANDLES */
/* #undef NVSHMEM_VERBOSE */
#define NVSHMEM_BUILD_TESTS
#define NVSHMEM_BUILD_EXAMPLES
#define NVSHMEM_GPUNETIO_SUPPORT
#define NVSHMEM_IBGDA_SUPPORT
/* #undef NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY */
/* #undef NVSHMEM_ENABLE_ALL_DEVICE_INLINING */
/* #undef NVSHMEM_HOSTLIB_ONLY */
/* #undef NVSHMEM_BUILD_P2P_ONLY */

#if defined (NVSHMEM_HOSTLIB_ONLY)
#undef NVSHMEM_IBGDA_SUPPORT
#undef NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY
#undef NVSHMEM_GPUNETIO_SUPPORT
#define NVSHMEM_ENABLE_ALL_DEVICE_INLINING
#endif

#if defined(__clang_llvm_bitcode_lib__)
#define NVSHMEM_ENABLE_ALL_DEVICE_INLINING
#endif

// When "transfer_device.cuh" is included, IBGDA and GPUNetIO are not supported with NVRTC.
#if defined(__CUDACC_RTC__) && (defined(NVSHMEM_ENABLE_ALL_DEVICE_INLINING) || \
                              defined(__NVSHMEM_NUMBA_SUPPORT__) || defined(NVSHMEM_BUILD_LTOIR_LIBRARY))
#undef NVSHMEM_IBGDA_SUPPORT
#undef NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY
#undef NVSHMEM_GPUNETIO_SUPPORT
#endif

// "transfer_device.cuh" requires <infiniband/mlx5dv.h> for IBGDA and GPUNetIO support,
// which is not available on all systems. Disable IBGDA and GPUNetIO support on such systems.
#if (defined(NVSHMEM_ENABLE_ALL_DEVICE_INLINING) || defined(__NVSHMEM_NUMBA_SUPPORT__) || \
     defined(NVSHMEM_BUILD_LTOIR_LIBRARY)) &&                                             \
    !__has_include(<infiniband/mlx5dv.h>)
#undef NVSHMEM_IBGDA_SUPPORT
#undef NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY
#undef NVSHMEM_GPUNETIO_SUPPORT
#endif
