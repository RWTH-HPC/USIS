<!-- source: OpenMP API Specification, section 23.1.5 (omp_ancestor_is_free_agent Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.1.5 omp_ancestor_is_free_agent Routine

Name: omp_ancestor_is_free_agent                          Properties: default
23
            Category: function

Return Type and Arguments
      Name                                         Type                          Properties
<return type>                                logical                       default
      level                                        integer                       default

Prototypes
                                                   C / C++
int omp_ancestor_is_free_agent(int level);
                                                   C / C++
                                                   Fortran
logical function omp_ancestor_is_free_agent(level)
integer level
                                                   Fortran
Effect
The omp_ancestor_is_free_agent routine returns true if the ancestor thread of the
encountering thread is a free-agent thread, for a given nested level of the encountering thread;
otherwise, it returns false. If the requested nesting level is outside the range of 0 and the nesting
level of the current task, as returned by the omp_get_level routine, the routine returns false.
12
Note – When the omp_ancestor_is_free_agent routine is called with a value of level
=omp_get_level, the routine has the same effect as the omp_is_free_agent routine.
15

Cross References
• omp_get_level Routine, see Section 21.14
• omp_is_free_agent Routine, see Section 23.1.4
• task Construct, see Section 14.1
• threadset Clause, see Section 14.8
