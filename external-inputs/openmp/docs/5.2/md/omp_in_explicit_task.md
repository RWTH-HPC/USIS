<!-- source: OpenMP API Specification, section 18.5.2 (omp_in_explicit_task) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.5.2 omp_in_explicit_task

Summary
The omp_in_explicit_task routine returns the value of the explicit-task-var ICV.

Format
                                                  C / C++
int omp_in_explicit_task(void);
                                                  C / C++
                                                  Fortran
logical function omp_in_explicit_task()
                                                   Fortran

Binding
The binding task set for an omp_in_explicit_task region is the generating task.
Effect
The omp_in_explicit_task routine returns the value of the explicit-task-var ICV, which
indicates whether the encountering region is an explicit task region.
Cross References
• explicit-task-var ICV, see Table 2.1
• task directive, see Section 12.5
