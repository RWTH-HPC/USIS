<!-- source: OpenMP API Specification, section 18.2.5 (omp_in_parallel) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.5 omp_in_parallel

Summary
The omp_in_parallel routine returns true if the active-levels-var ICV is greater than zero;
otherwise, it returns false.

Format
                                                 C / C++
int omp_in_parallel(void);
                                                 C / C++
                                                 Fortran
logical function omp_in_parallel()
                                                 Fortran
Binding
The binding task set for an omp_in_parallel region is the generating task.

Effect
The effect of the omp_in_parallel routine is to return true if the current task is enclosed by an
active parallel region, and the parallel region is enclosed by the outermost initial task
region on the device; otherwise it returns false.

Cross References
• active-levels-var ICV, see Table 2.1
• parallel directive, see Section 10.1
