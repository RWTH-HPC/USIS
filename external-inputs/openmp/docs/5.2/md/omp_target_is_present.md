<!-- source: OpenMP API Specification, section 18.8.3 (omp_target_is_present) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.8.3 omp_target_is_present

Summary
The omp_target_is_present routine tests whether a host pointer refers to storage that is
mapped to a given device.

Format
                                                C / C++
int omp_target_is_present(const void *ptr, int device_num);
                                                C / C++
                                                Fortran
integer(c_int) function omp_target_is_present(ptr, device_num) &
bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int
type(c_ptr), value :: ptr
integer(c_int), value :: device_num
                                                Fortran
Constraints on Arguments
The value of ptr must be a valid host pointer or NULL. The device_num argument must be a
conforming device number.

Binding
The binding task set for an omp_target_is_present region is the encountering task.

Effect
The omp_target_is_present routine returns true if device_num refers to the host device or
if ptr refers to storage that has corresponding storage in the device data environment of device
device_num. Otherwise, the routine returns false.
                                                Fortran
The omp_target_is_present routine requires an explicit interface and so might not be
provided in omp_lib.h.
                                                Fortran
Restrictions
Restrictions to the omp_target_is_present routine are as follows.
• When called from within a target region the effect is unspecified.

Cross References
• target directive, see Section 13.8
