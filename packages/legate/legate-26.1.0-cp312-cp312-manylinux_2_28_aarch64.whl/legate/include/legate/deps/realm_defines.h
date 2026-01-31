/*
 * Copyright 2025 Stanford University, NVIDIA Corporation
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * \file realm_defines.h
 * Public-facing definitions of variables configured at build time
 */

// ******************** IMPORTANT **************************
//
// This file is PURE C, **NOT** C++.
//
// ******************** IMPORTANT **************************

#ifndef REALM_DEFINES_H
#define REALM_DEFINES_H

#define REALM_VERSION "25.6.1-rc.4+90dc9818-dirty"
#define REALM_VERSION_MAJOR 25
#define REALM_VERSION_MINOR 6
#define REALM_VERSION_PATCH 1
#define REALM_VERSION_META  "-rc.4+90dc9818-dirty"

/* #undef DEBUG_REALM */

#define REALM_LIMIT_SYMBOL_VISIBILITY

#define COMPILE_TIME_MIN_LEVEL LEVEL_DEBUG

#define REALM_MAX_DIM 6

/* #undef REALM_USE_OPENMP */
/* #undef REALM_OPENMP_SYSTEM_RUNTIME */
/* #undef REALM_OPENMP_GOMP_SUPPORT */
/* #undef REALM_OPENMP_KMP_SUPPORT */

#define REALM_USE_PYTHON

#define REALM_USE_CUDA
/* #undef REALM_CUDA_DYNAMIC_LOAD */

/* #undef REALM_USE_HIP */

/* #undef REALM_USE_KOKKOS */

/* #undef REALM_USE_GASNET1 */
/* #undef REALM_USE_GASNETEX */

/* technically these are defined by per-conduit GASNet include files,
 * but we do it here as well for the benefit of applications that care
 */
/* #undef GASNET_CONDUIT_MPI */
/* #undef GASNET_CONDUIT_IBV */
/* #undef GASNET_CONDUIT_UDP */
/* #undef GASNET_CONDUIT_ARIES */
/* #undef GASNET_CONDUIT_GEMINI */
/* #undef GASNET_CONDUIT_PSM */
/* #undef GASNET_CONDUIT_UCX */
/* #undef GASNET_CONDUIT_OFI */

/* #undef REALM_USE_GASNETEX_WRAPPER */

/* #undef REALM_USE_MPI */
/* #undef REALM_MPI_HAS_COMM_SPLIT_TYPE */

#define REALM_USE_UCX
/* #undef REALM_UCX_DYNAMIC_LOAD */

/* #undef REALM_USE_LLVM */
/* #undef REALM_ALLOW_MISSING_LLVM_LIBS */

/* #undef REALM_USE_HDF5 */

#define REALM_USE_LIBDL
/* #undef REALM_USE_DLMOPEN */

/* #undef REALM_USE_HWLOC */

/* #undef REALM_USE_PAPI */

/* #undef REALM_USE_NVTX */

#define REALM_USE_CPPTRACE

/* #undef REALM_USE_KERNEL_AIO */
#define REALM_USE_LIBAIO

#define REALM_USE_SHM
/* #undef REALM_HAS_POSIX_FALLOCATE64 */
#define REALM_TIMERS_USE_RDTSC 1

/* #undef REALM_RESPONSIVE_TIMELIMIT */

#endif // REALM_DEFINES_H
