<!-- source: OpenMP API Specification, section 18.13.5 (omp_get_default_allocator) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.5 omp_get_default_allocator

Summary
The omp_get_default_allocator routine returns a handle to the memory allocator to be
used by allocation calls, allocate clauses and allocate and allocators directives that do
not specify an allocator.
Format
                                                        C / C++
omp_allocator_handle_t omp_get_default_allocator (void);
                                                        C / C++
                                                        Fortran
integer(kind=omp_allocator_handle_kind)&
function omp_get_default_allocator ()
                                                         Fortran
Binding
The binding task set for an omp_get_default_allocator region is the binding implicit task.
Effect
The effect of this routine is to return the value of the def-allocator-var ICV of the binding implicit
task.
Cross References
• Memory Allocators, see Section 6.2
• allocate clause, see Section 6.6
• allocate directive, see Section 6.5
• allocators directive, see Section 6.7
• def-allocator-var ICV, see Table 2.1
