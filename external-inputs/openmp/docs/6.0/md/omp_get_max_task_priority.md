<!-- source: OpenMP API Specification, section 23.1.1 (omp_get_max_task_priority Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.1.1 omp_get_max_task_priority Routine

Name: omp_get_max_task_priority                          Properties: all-device-threads-binding,
 8
            Category: function                                       ICV-retrieving

Return Type
            Name                                       Type                          Properties
10
            <return type>                              integer                       default

Prototypes
                                                       C / C++
int omp_get_max_task_priority(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_max_task_priority()
                                                       Fortran
Effect
The omp_get_max_task_priority routine returns the value of the max-task-priority-var
ICV, which determines the maximum value that can be specified in the priority clause.

Cross References
• max-task-priority-var ICV, see Table 3.1
• priority Clause, see Section 14.9
