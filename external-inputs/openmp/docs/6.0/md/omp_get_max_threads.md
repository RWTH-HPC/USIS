<!-- source: OpenMP API Specification, section 21.4 (omp_get_max_threads Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.4 omp_get_max_threads Routine

Name: omp_get_max_threads                                Properties: ICV-retrieving
 5
            Category: function

Return Type
            Name                                       Type                         Properties
 7
            <return type>                              integer                      default

Prototypes
                                                       C / C++
int omp_get_max_threads(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_max_threads()
                                                       Fortran
Effect
The value returned by omp_get_max_threads is the value of the first element of the
nthreads-var ICV of the current task; thus, the routine has the ICV retrieving property. Its return
value is an upper bound on the number of threads that could be used to form a new team if a parallel
region without a num_threads clause is encountered after execution returns from this routine.

Cross References
• nthreads-var ICV, see Table 3.1
• num_threads Clause, see Section 12.1.2
• parallel Construct, see Section 12.1
• Determining the Number of Threads for a parallel Region, see Section 12.1.1
