<!-- source: OpenMP API Specification, section 27.7 (omp_destroy_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.7 omp_destroy_allocator Routine

Name: omp_destroy_allocator                             Properties: all-device-threads-binding,
 9
            Category: subroutine                                    memory-management-routine

Arguments
            Name                                      Type                         Properties
11
            allocator                                 allocator_handle             intent(in), omp

Prototypes
                                                      C / C++
void omp_destroy_allocator(omp_allocator_handle_t allocator);
                                                      C / C++
                                                      Fortran
subroutine omp_destroy_allocator(allocator)
integer (kind=omp_allocator_handle_kind), intent(in) :: &
allocator
                                                      Fortran
Effect
The omp_destroy_allocator routine releases all resources used to implement the allocator
handle. If allocator is omp_null_allocator then this routine has no effect.

Restrictions
The restrictions to the omp_destroy_allocator routine are as follows:
• The allocator argument must not represent a predefined memory allocator.
• Accessing any memory allocated by the allocator after this call results in unspecified
behavior.
• Unless a requires directive with the dynamic_allocators clause is present in the
same compilation unit, using this routine in a target region results in unspecified behavior.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocators, see Section 8.2
• requires Directive, see Section 10.5
• target Construct, see Section 15.8
