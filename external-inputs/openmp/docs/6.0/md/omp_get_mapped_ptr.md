<!-- source: OpenMP API Specification, section 25.2.3 (omp_get_mapped_ptr Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.2.3 omp_get_mapped_ptr Routine

Name: omp_get_mapped_ptr                                 Properties: device-memory-
Category: function                                       information-routine, device-memory-
                                                                     routine, iso_c_binding
Return Type and Arguments
            Name                                        Type                        Properties
            <return type>                               c_ptr                       default
 9
            ptr                                         c_ptr                       intent(in), iso_c, value
            device_num                                  c_int                       iso_c, value

Prototypes
                                                       C / C++
void     *omp_get_mapped_ptr(const void *ptr, int device_num);
                                                       C / C++
                                                       Fortran
type (c_ptr) function omp_get_mapped_ptr(ptr, device_num) &
bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int
type (c_ptr), value, intent(in) :: ptr
integer (kind=c_int), value :: device_num
                                                        Fortran
Effect
The omp_get_mapped_ptr routine returns the associated device pointer for host pointer ptr on
device device_num. A call to this routine for a pointer that is not NULL and does not have an
associated pointer on the given device will return NULL. The routine returns NULL if unsuccessful.
Otherwise it returns the device pointer, which is ptr if device_num specifies the host device.
Cross References
• omp_get_initial_device Routine, see Section 24.10
