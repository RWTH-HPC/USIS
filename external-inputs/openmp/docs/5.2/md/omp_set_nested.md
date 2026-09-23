<!-- source: OpenMP API Specification, section 18.2.9 (omp_set_nested (Deprecated)) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.9 omp_set_nested (Deprecated)

Summary
The deprecated omp_set_nested routine enables or disables nested parallelism by setting the
max-active-levels-var ICV.

Format
                                                   C / C++
void omp_set_nested(int nested);
                                                   C / C++

                                                         Fortran
subroutine omp_set_nested(nested)
logical nested
                                                         Fortran
Binding
The binding task set for an omp_set_nested region is the generating task.

Effect
If the argument to omp_set_nested evaluates to true, the value of the max-active-levels-var
ICV is set to the number of active levels of parallelism that the implementation supports; otherwise,
if the value of max-active-levels-var is greater than 1 then it is set to 1. This routine has been
deprecated.

Cross References
• max-active-levels-var ICV, see Table 2.1
