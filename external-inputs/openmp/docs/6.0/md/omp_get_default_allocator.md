<!-- source: OpenMP API Specification, section 27.10 (omp_get_default_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.10 omp_get_default_allocator Routine

Name: omp_get_default_allocator                          Properties: binding-implicit-task-
12
      Category: function                                       binding, memory-management-routine

Return Type
      Name                                       Type                         Properties
14
      <return type>                              allocator_handle             default

Prototypes
                                                 C / C++
omp_allocator_handle_t omp_get_default_allocator(void);
                                                 C / C++
                                                 Fortran
integer (kind=omp_allocator_handle_kind) function &
omp_get_default_allocator()
                                                 Fortran
Effect
The omp_get_default_allocator routine returns the value of the def-allocator-var ICV of
the binding implicit task, which is a handle to the memory allocator to be used by allocation calls,
allocate clauses and allocate and allocators directives that do not specify an allocator.
This routine has the binding-implicit-task binding property, so the binding task set for an
omp_get_default_allocator region is the binding implicit task.

Cross References
• allocate Clause, see Section 8.6
• allocate Directive, see Section 8.5
• OpenMP allocator_handle Type, see Section 20.8.1
• allocators Construct, see Section 8.7
• Memory Allocators, see Section 8.2
• def-allocator-var ICV, see Table 3.1
