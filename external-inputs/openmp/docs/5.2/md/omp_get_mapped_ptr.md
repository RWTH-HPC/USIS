<!-- source: OpenMP API Specification, section 18.8.11 (omp_get_mapped_ptr) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.8.11 omp_get_mapped_ptr

Summary
The omp_get_mapped_ptr routine returns the device pointer that is associated with a host
pointer for a given device.
Format
                                                       C / C++
void * omp_get_mapped_ptr(const void *ptr, int device_num);
                                                       C / C++
                                                       Fortran
type(c_ptr) function omp_get_mapped_ptr(ptr, &
device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int
type(c_ptr), value :: ptr
integer(c_int), value :: device_num
                                                        Fortran

Constraints on Arguments
The device_num argument must be a conforming device number.
Binding
The binding task set for an omp_get_mapped_ptr region is the encountering task.
Effect
The omp_get_mapped_ptr routine returns the associated device pointer on device device_num.
A call to this routine for a pointer that is not NULL and does not have an associated pointer on the
given device will return NULL. The routine returns NULL if unsuccessful. Otherwise it returns the
device pointer, which is ptr if device_num is the value returned by
omp_get_initial_device().
                                                   Fortran
The omp_get_mapped_ptr routine requires an explicit interface and so might not be provided
in omp_lib.h.
                                                   Fortran
Execution Model Events
No events are associated with this routine.
Restrictions
Restrictions to the omp_get_mapped_ptr routine are as follows.
• When called from within a target region the effect is unspecified.

Cross References
• omp_get_initial_device, see Section 18.7.7
