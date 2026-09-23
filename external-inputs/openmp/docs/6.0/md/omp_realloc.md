<!-- source: OpenMP API Specification, section 27.11.5 (omp_realloc Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.11.5 omp_realloc Routine

Name: omp_realloc                                    Properties: iso_c_binding, memory-
            Category: function                                   allocating-routine, memory-
 2
                                                                 management-routine, memory-
                                                                 reallocating-routine, overloaded
Return Type and Arguments
            Name                                    Type                      Properties
            <return type>                           c_ptr                     default
            ptr                                     c_ptr                     iso_c, value
 4
            size                                    c_size_t                  iso_c, value
            allocator                               allocator_handle          value, omp
            free_allocator                          allocator_handle          value, omp

Prototypes
                                                       C
void *omp_realloc(void *ptr, size_t size,
omp_allocator_handle_t allocator,
omp_allocator_handle_t free_allocator);
                                                      C
                                                     C++
void *omp_realloc(void *ptr, size_t size,
omp_allocator_handle_t allocator = omp_null_allocator,
omp_allocator_handle_t free_allocator = omp_null_allocator);
                                                     C++
                                                    Fortran
type (c_ptr) function omp_realloc(ptr, size, allocator, &
free_allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t
type (c_ptr), value :: ptr
integer (kind=c_size_t), value :: size
integer (kind=omp_allocator_handle_kind), value :: allocator, &
free_allocator
                                                    Fortran
Effect
The omp_realloc routine is a memory-reallocating routine.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocating Routines, see Section 27.11
