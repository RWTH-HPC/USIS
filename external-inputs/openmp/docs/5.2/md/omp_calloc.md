<!-- source: OpenMP API Specification, section 18.13.8 (omp_calloc and omp_aligned_calloc) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_aligned_calloc -->

# 18.13.8 omp_calloc and omp_aligned_calloc

Summary
The omp_calloc and omp_aligned_calloc routines request a zero initialized memory
allocation from a memory allocator.
Format
                                                    C
void *omp_calloc(
size_t nmemb,
size_t size,
omp_allocator_handle_t allocator
);
void *omp_aligned_calloc(
size_t alignment,
size_t nmemb,
size_t size,
omp_allocator_handle_t allocator
);
                                                    C

                                                     C++
void *omp_calloc(
size_t nmemb,
size_t size,
omp_allocator_handle_t allocator=omp_null_allocator
);
void *omp_aligned_calloc(
size_t alignment,
size_t nmemb,
size_t size,
omp_allocator_handle_t allocator=omp_null_allocator
);
                                                     C++
                                                    Fortran
type(c_ptr) function omp_calloc(nmemb, size, allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t
integer(c_size_t), value :: nmemb, size
integer(omp_allocator_handle_kind), value :: allocator
16
type(c_ptr) function omp_aligned_calloc(alignment, nmemb, size, &
allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t
integer(c_size_t), value :: alignment, nmemb, size
integer(omp_allocator_handle_kind), value :: allocator
                                                    Fortran
Constraints on Arguments
Unless dynamic_allocators appears on a requires directive in the same compilation unit,
omp_calloc and omp_aligned_calloc invocations that appear in target regions must
not pass omp_null_allocator as the allocator argument, which must be a constant expression
that evaluates to one of the predefined memory allocator values. The alignment argument to
omp_aligned_calloc must be a power of two and the size argument must be a multiple of
alignment.

Binding
The binding task set for an omp_calloc or omp_aligned_calloc region is the generating
task.

Effect
The omp_calloc and omp_aligned_calloc routines request a memory allocation from the
specified memory allocator for an array of nmemb elements each of which has a size of size bytes.
If the allocator argument is omp_null_allocator the memory allocator used by the routines
will be the one specified by the def-allocator-var ICV of the binding implicit task. Upon success
they return a pointer to the allocated memory. Otherwise, the behavior that the fallback trait of
the allocator specifies will be followed. Any memory allocated by these routines will be set to zero
before returning. If either nmemb or size is 0, omp_calloc will return NULL.
Memory allocated by omp_calloc will be byte-aligned to at least the maximum of the alignment
required by malloc and the alignment trait of the allocator. Memory allocated by
omp_aligned_calloc will be byte-aligned to at least the maximum of the alignment required
by malloc, the alignment trait of the allocator and the alignment argument value.
                                                 Fortran
The omp_calloc and omp_aligned_calloc routines require an explicit interface and so
might not be provided in omp_lib.h.
                                                 Fortran
Cross References
• Memory Allocators, see Section 6.2
• def-allocator-var ICV, see Table 2.1
• requires directive, see Section 8.2
• target directive, see Section 13.8
