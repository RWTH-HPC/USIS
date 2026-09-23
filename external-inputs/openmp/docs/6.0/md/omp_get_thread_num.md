<!-- source: OpenMP API Specification, section 21.3 (omp_get_thread_num Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.3 omp_get_thread_num Routine

Name: omp_get_thread_num                                 Properties: default
12
      Category: function

Return Type
      Name                                        Type                        Properties
14
      <return type>                               integer                     default

Prototypes
                                                 C / C++
int omp_get_thread_num(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_thread_num()
                                                 Fortran
Effect
The omp_get_thread_num routine returns the thread number of the calling thread, within the
team that is executing the parallel region to which the routine region binds. For assigned threads,
the thread number is an integer between 0 and one less than the value returned by
omp_get_num_threads, inclusive. The thread number of the primary thread of the team is 0.
For unassigned threads, the thread number is the value omp_unassigned_thread.

Cross References
• Predefined Identifiers, see Section 20.1
• omp_get_num_threads Routine, see Section 21.2
