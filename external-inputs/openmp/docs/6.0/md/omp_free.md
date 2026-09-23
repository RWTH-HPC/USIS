<!-- source: OpenMP API Specification, section 27.12 (omp_free Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.12 omp_free Routine

Name: omp_free                                        Properties: iso_c_binding, memory-
 2
      Category: subroutine                                  management-routine, overloaded

Arguments
      Name                                     Type                        Properties
ptr                                      c_ptr                       iso_c, value
      allocator                                allocator_handle            value, omp

Prototypes
                                                   C
void omp_free(void *ptr, omp_allocator_handle_t allocator);
                                                  C
                                                 C++
void omp_free(void *ptr,
omp_allocator_handle_t allocator = omp_null_allocator);
                                                C++
                                               Fortran
subroutine omp_free(ptr, allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr
type (c_ptr), value :: ptr
integer (kind=omp_allocator_handle_kind), value :: allocator
                                               Fortran
Effect
The omp_free routine deallocates the memory to which the ptr argument points. If the allocator
argument is omp_null_allocator, the implementation will determine that value
automatically. If ptr is NULL, no operation is performed.
                                                 C++
The C++ version of the omp_free routine has the overloaded property since it is an overloaded
routine for which the allocator argument may be omitted, in which case the effect is as if
omp_null_allocator is specified.
                                                 C++

Restrictions
The restrictions to the omp_free routine are as follows:
• The ptr argument must have been returned by a memory-allocating routine.
• If the allocator argument is specified it must be the memory allocator to which the allocation
request was made.
• Using omp_free on memory that was already deallocated or that was allocated by an
allocator that has already been destroyed with omp_destroy_allocator results in
unspecified behavior.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocating Routines, see Section 27.11
• Memory Allocators, see Section 8.2
• omp_destroy_allocator Routine, see Section 27.7
