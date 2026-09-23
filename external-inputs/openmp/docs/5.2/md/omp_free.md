<!-- source: OpenMP API Specification, section 18.13.7 (omp_free) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.7 omp_free

Summary
The omp_free routine deallocates previously allocated memory.
Format
                                                         C
void omp_free (void *ptr, omp_allocator_handle_t allocator);
                                                         C
                                                        C++
void omp_free(
void *ptr,
omp_allocator_handle_t allocator=omp_null_allocator
);
                                                       C++
                                                      Fortran
subroutine omp_free(ptr, allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr
type(c_ptr), value :: ptr
integer(omp_allocator_handle_kind), value :: allocator
                                                      Fortran
Binding
The binding task set for an omp_free region is the generating task.

Effect
The omp_free routine deallocates the memory to which ptr points. The ptr argument must have
been returned by an OpenMP allocation routine. If the allocator argument is specified it must be
the memory allocator to which the allocation request was made. If the allocator argument is
omp_null_allocator the implementation will determine that value automatically. If ptr is
NULL, no operation is performed.
                                                Fortran
The omp_free routine requires an explicit interface and so might not be provided in
omp_lib.h.
                                                Fortran
Restrictions
The restrictions to the omp_free routine are as follows:
• Using omp_free on memory that was already deallocated or that was allocated by an allocator
that has already been destroyed with omp_destroy_allocator results in unspecified
behavior.
Cross References
• Memory Allocators, see Section 6.2
• omp_destroy_allocator, see Section 18.13.3
