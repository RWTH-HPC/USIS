<!-- source: OpenMP API Specification, section 18.2.20 (omp_get_active_level) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.20 omp_get_active_level

Summary
The omp_get_active_level routine returns the value of the active-levels-var ICV.

Format
                                                       C / C++
int omp_get_active_level(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_active_level()
                                                       Fortran
Binding
The binding task set for the an omp_get_active_level region is the generating task.

Effect
The effect of the omp_get_active_level routine is to return the number of nested active
parallel regions enclosing the current task such that all of the parallel regions are enclosed
by the outermost initial task region on the current device.

Cross References
• active-levels-var ICV, see Table 2.1
• parallel directive, see Section 10.1
