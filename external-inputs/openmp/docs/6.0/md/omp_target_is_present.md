<!-- source: OpenMP API Specification, section 25.2.1 (omp_target_is_present Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.2.1 omp_target_is_present Routine

Name: omp_target_is_present                             Properties: device-memory-
Category: function                                      information-routine, device-memory-
                                                                    routine, iso_c_binding
Return Type and Arguments
            Name                                      Type                        Properties
            <return type>                             c_int                       default
24
            ptr                                       c_ptr                       intent(in), iso_c, value
            device_num                                c_int                       iso_c, value

Prototypes
                                                      C / C++
int omp_target_is_present(const void *ptr, int device_num);
                                                      C / C++

                                                  Fortran
integer (kind=c_int) function omp_target_is_present(ptr, &
device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr
type (c_ptr), value, intent(in) :: ptr
integer (kind=c_int), value :: device_num
                                                  Fortran
Effect
The omp_target_is_present routine returns a non-zero value if device_num refers to the
host device or if ptr refers to storage that has corresponding storage in the device data environment
of device device_num. Otherwise, the routine returns zero. If ptr is NULL. the routine returns zero.
Thus, the omp_target_is_present routine tests whether a host pointer refers to storage that
is mapped to a given device.
Restrictions
Restrictions to the omp_target_is_present routine are as follows:
• The value of ptr must be a valid host pointer or NULL.
