<!-- source: OpenMP API Specification, section 21.7 (omp_set_dynamic Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.7 omp_set_dynamic Routine

Name: omp_set_dynamic                                  Properties: ICV-modifying
 5
            Category: subroutine

Arguments
            Name                                       Type                      Properties
 7
            dynamic_threads                            logical                   default

Prototypes
                                                       C / C++
void omp_set_dynamic(int dynamic_threads);
                                                       C / C++
                                                       Fortran
subroutine omp_set_dynamic(dynamic_threads)
logical dynamic_threads
                                                       Fortran
Effect
For implementations that support dynamic adjustment of the number of threads, if the argument to
omp_set_dynamic evaluates to true, dynamic adjustment is enabled for the current task by
setting the value of the dyn-var ICV to true; otherwise, dynamic adjustment is disabled for the
current task by setting the value of the dyn-var ICV to false. For implementations that do not
support dynamic adjustment of the number of threads, this routine has no effect: the value of
dyn-var remains false.

Cross References
• dyn-var ICV, see Table 3.1
