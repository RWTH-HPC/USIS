<!-- source: OpenMP API Specification, section 18.7.2 (omp_set_default_device) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.2 omp_set_default_device

Summary
The omp_set_default_device routine controls the default target device by assigning the
value of the default-device-var ICV.

Format
                                                         C / C++
void omp_set_default_device(int device_num);
                                                         C / C++
                                                         Fortran
subroutine omp_set_default_device(device_num)
integer device_num
                                                         Fortran
Binding
The binding task set for an omp_set_default_device region is the generating task.

Effect
The effect of this routine is to set the value of the default-device-var ICV of the current task to the
value specified in the argument. When called from within a target region the effect of this
routine is unspecified.

Cross References
• default-device-var ICV, see Table 2.1
• target directive, see Section 13.8
