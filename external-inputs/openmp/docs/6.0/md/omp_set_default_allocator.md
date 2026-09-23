<!-- source: OpenMP API Specification, section 27.9 (omp_set_default_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.9 omp_set_default_allocator Routine

Name: omp_set_default_allocator                          Properties: binding-implicit-task-
 9
            Category: subroutine                                     binding, memory-management-routine

Arguments
            Name                                       Type                         Properties
11
            allocator                                  allocator_handle             omp, intent(in)

Prototypes
                                                       C / C++
void omp_set_default_allocator(omp_allocator_handle_t allocator);
                                                       C / C++
                                                       Fortran
subroutine omp_set_default_allocator(allocator)
integer (kind=omp_allocator_handle_kind), intent(in) :: &
allocator
                                                       Fortran
Effect
The effect of the omp_set_default_allocator is to set the value of the def-allocator-var
ICV of the binding implicit task to the value specified in the allocator argument. Thus, it sets the
default memory allocator to be used by allocation calls, allocate clauses and allocate and
allocators directives that do not specify an allocator. This routine has the binding-implicit-task
binding property so the binding task set for an omp_set_default_allocator region is the
binding implicit task.

Restrictions
The restrictions to the omp_set_default_allocator routine are as follows:
• The allocator argument must be a valid memory allocator handle.

Cross References
• allocate Clause, see Section 8.6
• allocate Directive, see Section 8.5
• OpenMP allocator_handle Type, see Section 20.8.1
• allocators Construct, see Section 8.7
• Memory Allocators, see Section 8.2
• def-allocator-var ICV, see Table 3.1
