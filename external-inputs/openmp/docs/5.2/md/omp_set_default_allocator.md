<!-- source: OpenMP API Specification, section 18.13.4 (omp_set_default_allocator) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.4 omp_set_default_allocator

Summary
The omp_set_default_allocator routine sets the default memory allocator to be used by
allocation calls, allocate clauses and allocate and allocators directives that do not
specify an allocator.
Format
                                                   C / C++
void omp_set_default_allocator (omp_allocator_handle_t allocator);
                                                   C / C++
                                                   Fortran
subroutine omp_set_default_allocator ( allocator )
integer(kind=omp_allocator_handle_kind),intent(in) :: allocator
                                                   Fortran
Constraints on Arguments
The allocator argument must be a valid memory allocator handle.
Binding
The binding task set for an omp_set_default_allocator region is the binding implicit task.
Effect
The effect of this routine is to set the value of the def-allocator-var ICV of the binding implicit task
to the value specified in the allocator argument.
Cross References
• Memory Allocators, see Section 6.2
• allocate clause, see Section 6.6
• allocate directive, see Section 6.5
• allocators directive, see Section 6.7
• def-allocator-var ICV, see Table 2.1
