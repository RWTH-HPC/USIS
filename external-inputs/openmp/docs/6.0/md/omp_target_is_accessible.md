<!-- source: OpenMP API Specification, section 25.2.2 (omp_target_is_accessible Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.2.2 omp_target_is_accessible Routine

Name: omp_target_is_accessible                           Properties: device-memory-
Category: function                                       information-routine, device-memory-
                                                               routine, iso_c_binding
Return Type and Arguments
      Name                                        Type                        Properties
      <return type>                               c_int                       default
ptr                                         c_ptr                       intent(in), iso_c, value
      size                                        c_size_t                    iso_c, positive, value
      device_num                                  c_int                       iso_c, value

Prototypes
                                                 C / C++
int omp_target_is_accessible(const void *ptr, size_t size,
int device_num);
                                                 C / C++
                                                 Fortran
integer (kind=c_int) function omp_target_is_accessible(ptr, &
size, device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value, intent(in) :: ptr
integer (kind=c_size_t), value :: size
integer (kind=c_int), value :: device_num
                                                  Fortran

Effect
The omp_target_is_accessible routine returns a non-zero value if the storage of size bytes
that corresponds to the address range starting at the address given by ptr is accessible from device
device_num. Otherwise, it returns zero. If ptr is NULL, the routine returns zero. The value of ptr is
interpreted as an address in the address space of the specified device.
