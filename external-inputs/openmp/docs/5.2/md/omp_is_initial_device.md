<!-- source: OpenMP API Specification, section 18.7.6 (omp_is_initial_device) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.6 omp_is_initial_device

Summary
The omp_is_initial_device routine returns true if the current task is executing on the host
device; otherwise, it returns false.

Format
                                                         C / C++
int omp_is_initial_device(void);
                                                         C / C++
                                                         Fortran
logical function omp_is_initial_device()
                                                          Fortran
Binding
The binding task set for an omp_is_initial_device region is the generating task.

Effect
The effect of this routine is to return true if the current task is executing on the host device;
otherwise, it returns false.
