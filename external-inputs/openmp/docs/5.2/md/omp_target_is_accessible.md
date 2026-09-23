<!-- source: OpenMP API Specification, section 18.8.4 (omp_target_is_accessible) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.8.4 omp_target_is_accessible

Summary
The omp_target_is_accessible routine tests whether host memory is accessible from a
given device.

Format
                                                         C / C++
int omp_target_is_accessible( const void *ptr, size_t size,
int device_num);
                                                         C / C++
                                                         Fortran
integer(c_int) function omp_target_is_accessible( &
ptr, size, device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t, c_int
type(c_ptr), value :: ptr
integer(c_size_t), value :: size
integer(c_int), value :: device_num
                                                         Fortran
Constraints on Arguments
The value of ptr must be a valid host pointer or NULL. The device_num argument must be a
conforming device number.

Binding
The binding task set for an omp_target_is_accessible region is the encountering task.

Effect
This routine returns true if the storage of size bytes starting at the address given by ptr is accessible
from device device_num. Otherwise, it returns false.
                                                         Fortran
The omp_target_is_accessible routine requires an explicit interface and so might not be
provided in omp_lib.h.
                                                         Fortran
Restrictions
Restrictions to the omp_target_is_accessible routine are as follows.
• When called from within a target region the effect is unspecified.

Cross References
• target directive, see Section 13.8
