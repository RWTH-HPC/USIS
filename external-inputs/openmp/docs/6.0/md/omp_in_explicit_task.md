<!-- source: OpenMP API Specification, section 23.1.2 (omp_in_explicit_task Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.1.2 omp_in_explicit_task Routine

Name: omp_in_explicit_task                           Properties: ICV-retrieving
 2
      Category: function

Return Type
      Name                                       Type                   Properties
 4
      <return type>                              logical                default

Prototypes
                                                 C / C++
int omp_in_explicit_task(void);
                                                 C / C++
                                                 Fortran
logical function omp_in_explicit_task()
                                                 Fortran
Effect
The omp_in_explicit_task routine returns the value of the explicit-task-var ICV, which
indicates whether the encountering task is an explicit task region.

Cross References
• explicit-task-var ICV, see Table 3.1
• task Construct, see Section 14.1
