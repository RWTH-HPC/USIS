<!-- source: OpenMP API Specification, section 18.7.5 (omp_get_device_num) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.5 omp_get_device_num

Summary
The omp_get_device_num routine returns the device number of the device on which the
calling thread is executing.

Format
                                                         C / C++
int omp_get_device_num(void);
                                                         C / C++
                                                         Fortran
integer function omp_get_device_num()
                                                          Fortran
Binding
The binding task set for an omp_get_device_num region is the generating task.

Effect
The omp_get_device_num routine returns the device number of the device on which the
calling thread is executing. When called on the host device, it will return the same value as the
omp_get_initial_device routine.
