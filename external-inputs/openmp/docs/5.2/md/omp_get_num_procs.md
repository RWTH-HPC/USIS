<!-- source: OpenMP API Specification, section 18.7.1 (omp_get_num_procs) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.1 omp_get_num_procs

Summary
The omp_get_num_procs routine returns the number of processors available to the device.
Format
                                                   C / C++
int omp_get_num_procs(void);
                                                   C / C++
                                                   Fortran
integer function omp_get_num_procs()
                                                   Fortran
Binding
The binding thread set for an omp_get_num_procs region is all threads on a device. The effect
of executing this routine is not related to any specific region corresponding to any construct or API
routine.

Effect
The omp_get_num_procs routine returns the number of processors that are available to the
device at the time the routine is called. This value may change between the time that it is
determined by the omp_get_num_procs routine and the time that it is read in the calling
context due to system actions outside the control of the OpenMP implementation.
