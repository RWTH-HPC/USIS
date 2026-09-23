<!-- source: OpenMP API Specification, section 18.5.1 (omp_get_max_task_priority) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.5.1 omp_get_max_task_priority

Summary
The omp_get_max_task_priority routine returns the maximum value that can be specified
in the priority clause.

Format
                                                  C / C++
int omp_get_max_task_priority(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_max_task_priority()
                                                   Fortran
Binding
The binding thread set for an omp_get_max_task_priority region is all threads on the
device. The effect of executing this routine is not related to any specific region that corresponds to
any construct or API routine.
Effect
The omp_get_max_task_priority routine returns the value of the max-task-priority-var
ICV, which determines the maximum value that can be specified in the priority clause.

Cross References
• max-task-priority-var ICV, see Table 2.1
• priority clause, see Section 12.4
