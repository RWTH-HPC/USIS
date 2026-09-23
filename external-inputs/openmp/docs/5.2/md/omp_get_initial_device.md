<!-- source: OpenMP API Specification, section 18.7.7 (omp_get_initial_device) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.7 omp_get_initial_device

Summary
The omp_get_initial_device routine returns a device number that represents the host
device.

Format
                                                  C / C++
int omp_get_initial_device(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_initial_device()
                                                  Fortran
Binding
The binding task set for an omp_get_initial_device region is the generating task.

Effect
The effect of this routine is to return the device number of the host device. The value of the device
number is the value returned by the omp_get_num_devices routine. When called from within
a target region the effect of this routine is unspecified.

Cross References
• target directive, see Section 13.8
