<!-- source: OpenMP API Specification, section 21.1 (omp_set_num_threads Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.1 omp_set_num_threads Routine

Name: omp_set_num_threads                                  Properties: ICV-modifying
 6
            Category: subroutine

Arguments
            Name                                         Type                         Properties
 8
            num_threads                                  integer                      positive

Prototypes
                                                        C / C++
void omp_set_num_threads(int num_threads);
                                                        C / C++
                                                        Fortran
subroutine omp_set_num_threads(num_threads)
integer num_threads
                                                         Fortran
Effect
The effect of this routine is to set the value of the first element of the nthreads-var ICV of the
current task to the value specified in the argument. Thus, the routine has the ICV modifying
property, through which it affects the number of threads to be used for subsequent parallel
regions that do not specify a num_threads clause.

Cross References
• nthreads-var ICV, see Table 3.1
• num_threads Clause, see Section 12.1.2
• parallel Construct, see Section 12.1
• Determining the Number of Threads for a parallel Region, see Section 12.1.1
