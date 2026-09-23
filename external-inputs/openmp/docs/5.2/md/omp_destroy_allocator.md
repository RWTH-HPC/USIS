<!-- source: OpenMP API Specification, section 18.13.3 (omp_destroy_allocator) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.3 omp_destroy_allocator

Summary
The omp_destroy_allocator routine releases all resources used by the allocator handle.

Format
                                                         C / C++
void omp_destroy_allocator (omp_allocator_handle_t allocator);
                                                         C / C++
                                                         Fortran
subroutine omp_destroy_allocator ( allocator )
integer(kind=omp_allocator_handle_kind),intent(in) :: allocator
                                                         Fortran
Constraints on Arguments
The allocator argument must not represent a predefined memory allocator.

Binding
The binding thread set for an omp_destroy_allocator region is all threads on a device. The
effect of executing this routine is not related to any specific region that corresponds to any construct
or API routine.

Effect
The omp_destroy_allocator routine releases all resources used to implement the allocator
handle. If allocator is omp_null_allocator then this routine will have no effect.

Restrictions
The restrictions to the omp_destroy_allocator routine are as follows:
• Accessing any memory allocated by the allocator after this call results in unspecified behavior.
• Unless a requires directive with the dynamic_allocators clause is present in the same
compilation unit, using this routine in a target region results in unspecified behavior.

Cross References
• Memory Allocators, see Section 6.2
• requires directive, see Section 8.2
• target directive, see Section 13.8
