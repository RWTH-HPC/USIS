<!-- source: OpenMP API Specification, section 18.7.3 (omp_get_default_device) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.3 omp_get_default_device

Summary
The omp_get_default_device routine returns the default target device.

Format
                                                         C / C++
int omp_get_default_device(void);
                                                         C / C++

                                               Fortran
integer function omp_get_default_device()
                                               Fortran
Binding
The binding task set for an omp_get_default_device region is the generating task.

Effect
The omp_get_default_device routine returns the value of the default-device-var ICV of the
current task. When called from within a target region the effect of this routine is unspecified.

Cross References
• default-device-var ICV, see Table 2.1
• target directive, see Section 13.8
