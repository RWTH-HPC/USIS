<!-- source: OpenMP API Specification, section 18.2.6 (omp_set_dynamic) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.6 omp_set_dynamic

Summary
The omp_set_dynamic routine enables or disables dynamic adjustment of the number of
threads available for the execution of subsequent parallel regions by setting the value of the
dyn-var ICV.

Format
                                                      C / C++
void omp_set_dynamic(int dynamic_threads);
                                                      C / C++

                                                      Fortran
subroutine omp_set_dynamic(dynamic_threads)
logical dynamic_threads
                                                      Fortran
Binding
The binding task set for an omp_set_dynamic region is the generating task.

Effect
For implementations that support dynamic adjustment of the number of threads, if the argument to
omp_set_dynamic evaluates to true, dynamic adjustment is enabled for the current task;
otherwise, dynamic adjustment is disabled for the current task. For implementations that do not
support dynamic adjustment of the number of threads, this routine has no effect: the value of
dyn-var remains false.

Cross References
• dyn-var ICV, see Table 2.1
