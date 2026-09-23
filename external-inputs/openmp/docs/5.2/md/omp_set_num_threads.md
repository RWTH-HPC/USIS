<!-- source: OpenMP API Specification, section 18.2.1 (omp_set_num_threads) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.1 omp_set_num_threads

Summary
The omp_set_num_threads routine affects the number of threads to be used for subsequent
parallel regions that do not specify a num_threads clause, by setting the value of the first
element of the nthreads-var ICV of the current task.

Format
                                                       C / C++
void omp_set_num_threads(int num_threads);
                                                       C / C++

                                                   Fortran
subroutine omp_set_num_threads(num_threads)
integer num_threads
                                                   Fortran
Constraints on Arguments
The value of the argument passed to this routine must evaluate to a positive integer, or else the
behavior of this routine is implementation defined.

Binding
The binding task set for an omp_set_num_threads region is the generating task.

Effect
The effect of this routine is to set the value of the first element of the nthreads-var ICV of the
current task to the value specified in the argument.

Cross References
• Determining the Number of Threads for a parallel Region, see Section 10.1.1
• nthreads-var ICV, see Table 2.1
• num_threads clause, see Section 10.1.2
• parallel directive, see Section 10.1
