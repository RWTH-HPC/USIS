<!-- source: OpenMP API Specification, section 18.13.9 (omp_realloc) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.9 omp_realloc

Summary
The omp_realloc routine deallocates previously allocated memory and requests a memory
allocation from a memory allocator.

Format
                                                     C
void *omp_realloc(
void *ptr,
size_t size,
omp_allocator_handle_t allocator,
omp_allocator_handle_t free_allocator
);
                                                     C

                                                         C++
void *omp_realloc(
void *ptr,
size_t size,
omp_allocator_handle_t allocator=omp_null_allocator,
omp_allocator_handle_t free_allocator=omp_null_allocator
);
                                                        C++
                                                       Fortran
type(c_ptr) &
function omp_realloc(ptr, size, allocator, free_allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t
type(c_ptr), value :: ptr
integer(c_size_t), value :: size
integer(omp_allocator_handle_kind), value :: allocator, free_allocator
                                                       Fortran
Constraints on Arguments
Unless a dynamic_allocators clause appears on a requires directive in the same
compilation unit, omp_realloc invocations that appear in target regions must not pass
omp_null_allocator as the allocator or free_allocator argument, which must be constant
expressions that evaluate to one of the predefined memory allocator values.

Binding
The binding task set for an omp_realloc region is the generating task.

Effect
The omp_realloc routine deallocates the memory to which ptr points and requests a new
memory allocation of size bytes from the specified memory allocator. If the free_allocator
argument is specified, it must be the memory allocator to which the previous allocation request was
made. If the free_allocator argument is omp_null_allocator the implementation will
determine that value automatically. If the allocator argument is omp_null_allocator the
behavior is as if the memory allocator that allocated the memory to which ptr argument points is
passed to the allocator argument. Upon success it returns a (possibly moved) pointer to the
allocated memory and the contents of the new object shall be the same as that of the old object
prior to deallocation, up to the minimum size of old allocated size and size. Any bytes in the new
object beyond the old allocated size will have unspecified values. If the allocation failed, the
behavior that the fallback trait of the allocator specifies will be followed. If ptr is NULL,
omp_realloc will behave the same as omp_alloc with the same size and allocator arguments.
If size is 0, omp_realloc will return NULL and the old allocation will be deallocated. If size is
not 0, the old allocation will be deallocated if and only if the function returns a non-null value.
Memory allocated by omp_realloc will be byte-aligned to at least the maximum of the
alignment required by malloc and the alignment trait of the allocator.

                                               Fortran
The omp_realloc routine requires an explicit interface and so might not be provided in
omp_lib.h.
                                               Fortran
Restrictions
The restrictions to the omp_realloc routine are as follows:
• The ptr argument must have been returned by an OpenMP allocation routine.
• Using omp_realloc on memory that was already deallocated or that was allocated by an
allocator that has already been destroyed with omp_destroy_allocator results in
unspecified behavior.

Cross References
• Memory Allocators, see Section 6.2
• omp_alloc and omp_aligned_alloc, see Section 18.13.6
• omp_destroy_allocator, see Section 18.13.3
• requires directive, see Section 8.2
• target directive, see Section 13.8
