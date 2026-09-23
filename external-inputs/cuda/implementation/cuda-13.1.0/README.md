# CUDA 13.1.0 — runtime API headers (vendored)

> Only this README is in git. The files it describes are not redistributed (see `why_not_vendored` in `workflow/fetch/manifest.json`); `python3 workflow/fetch/fetch.py` downloads them and checks each against the sha256 pinned there. The public source is NVIDIA's CUDA redist archive `cuda_cudart-linux-x86_64-13.1.80-archive.tar.xz` (listed in `redistrib_13.1.0.json`), whose two headers are byte-identical to the cluster copies described below and whose `LICENSE` is this `EULA.txt`.

- **Files**: `include/cuda_runtime_api.h` — the CUDA Runtime API declarations
  (`cudaMalloc`, `cudaMemcpy`, `cudaStreamSynchronize`, ...) with NVIDIA's
  doxygen comments intact; the input `workflow/extract/cuda/adapter.py` reads.
  And `include/cuda_device_runtime_api.h` — the **device** runtime's own header,
  read by `workflow/classify/cuda/classify_cuda.py` for one thing:
  `execution.launch`. It is the authority on which runtime routines device code
  may call, and it disagrees with the qualifier that was previously used to infer
  that (see "Why the device header" below). Copied 2026-09-12, sha256
  `d3110e08d9dbe604058dfae1d5c54c58b9385ce54b32b941b79b850eadc4765f`.
- **Origin**: the CUDA Toolkit 13.1.0 installation on the RWTH HPC cluster,
  `/cvmfs/software.hpc.rwth.de/Linux/RH9/x86_64/intel/sapphirerapids/software/CUDA/13.1.0/targets/x86_64-linux/include/cuda_runtime_api.h`.
  The toolkit's `version.json` reports CUDA SDK `13.1.20251125` and cudart
  `13.1.80`; the header's own `CUDART_VERSION` is `13010`.
- **Copied**: 2026-09-11, byte for byte
  (sha256 `8b8a86cab3470a0673de17332ac8a71dc8197964e4f931f1e0fe4ced09eaa5c3`).
- **Licence**: NVIDIA proprietary. The header is one of the toolkit's
  "Licensed Deliverables"; the toolkit's End User License Agreement is copied
  alongside it as `EULA.txt`, from the root of the same installation. Vendored
  with the project owner's approval (2026-09-11), on the same footing as the
  NVSHMEM headers under `external-inputs/nvshmem/implementation/`.
- **Scope**: these two headers. The other files they `#include`
  (`crt/host_defines.h`, `builtin_types.h`, ...) are not vendored — nothing here
  reads type definitions, only declarations and doxygen text. The device
  runtime's routines are still **not corpus entries**: `identity.model: "cuda"`
  means the host-callable CUDA Runtime API, and the device header is read as
  evidence about those routines, not as a second API surface to extract.

## Why the device header

`execution.launch` was derived from the `__cudart_builtin__` qualifier that
`cuda_runtime_api.h` puts on 52 routines, on the reading that it marks the ones
the device runtime also provides. Checked against the device runtime's own
header on 2026-09-12, that reading is wrong for 22 of the 52:
`cudaMallocManaged`, `cudaGetDeviceProperties`, `cudaStreamCreateWithPriority`,
`cudaStreamGet{Flags,Id,Priority,Device,Attribute}`, `cudaStreamSetAttribute`,
`cudaFuncSetAttribute`,
`cudaFuncGetName`, `cudaFuncGetParamInfo`, the three occupancy helpers,
`cudaStreamCopyAttributes`, `cudaStreamAttachMemAsync`,
`cudaDeviceGet{HostAtomicCapabilities,P2PAtomicCapabilities,P2PAttribute,StreamPriorityRange,Texture1DLinearMaxWidth}`
carry the qualifier and are not declared `__device__` anywhere. The qualifier
says the runtime may supply a builtin implementation; it is not a claim about
device-callability. It also misses one in the other direction —
`cudaGraphLaunch` is declared `__device__` without carrying it.

The device header also states its own deprecations, which the runtime header
only hints at through a doxygen alias: `cudaDeviceSynchronize` is declared
`__CDPRT_DEPRECATED` under the comment `// cudaDeviceSynchronize is removed on
sm_90+`. Its entry keeps `launch: "cpu+gpu"` — the declaration is there — and
says so in the classification note rather than claiming an unqualified yes.

## Notice

The header requires that its disclaimer and U.S. Government End Users notice
accompany user documentation of software that uses it. Reproduced verbatim:

```
Copyright 1993-2024 NVIDIA Corporation.  All rights reserved.

NOTICE TO LICENSEE:

This source code and/or documentation ("Licensed Deliverables") are
subject to NVIDIA intellectual property rights under U.S. and
international Copyright laws.

These Licensed Deliverables contained herein is PROPRIETARY and
CONFIDENTIAL to NVIDIA and is being provided under the terms and
conditions of a form of NVIDIA software license agreement by and
between NVIDIA and Licensee ("License Agreement") or electronically
accepted by Licensee.  Notwithstanding any terms or conditions to
the contrary in the License Agreement, reproduction or disclosure
of the Licensed Deliverables to any third party without the express
written consent of NVIDIA is prohibited.

NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
LICENSE AGREEMENT, NVIDIA MAKES NO REPRESENTATION ABOUT THE
SUITABILITY OF THESE LICENSED DELIVERABLES FOR ANY PURPOSE.  IT IS
PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF ANY KIND.
NVIDIA DISCLAIMS ALL WARRANTIES WITH REGARD TO THESE LICENSED
DELIVERABLES, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY,
NONINFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
LICENSE AGREEMENT, IN NO EVENT SHALL NVIDIA BE LIABLE FOR ANY
SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, OR ANY
DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
OF THESE LICENSED DELIVERABLES.

U.S. Government End Users.  These Licensed Deliverables are a
"commercial item" as that term is defined at 48 C.F.R. 2.101 (OCT
1995), consisting of "commercial computer software" and "commercial
computer software documentation" as such terms are used in 48
C.F.R. 12.212 (SEPT 1995) and is provided to the U.S. Government
only as a commercial end item.  Consistent with 48 C.F.R.12.212 and
48 C.F.R. 227.7202-1 through 227.7202-4 (JUNE 1995), all
U.S. Government End Users acquire the Licensed Deliverables with
only those rights set forth herein.

Any use of the Licensed Deliverables in individual and commercial
software must include, in the user documentation and internal
comments to the code, the above Disclaimer and U.S. Government End
Users Notice.
```

## Refreshing for a new CUDA release

1. Copy the new toolkit's `targets/x86_64-linux/include/cuda_runtime_api.h`
   and `EULA.txt` into a new `cuda-<version>/` directory beside this one.
2. Point `_HEADER_PATH` in `workflow/extract/cuda/adapter.py` at it and
   rebuild; the adapter raises rather than guessing if a routine is declared
   twice in the host C view or a parameter is not a plain declarator.
3. Update this README's version, date and checksum.
