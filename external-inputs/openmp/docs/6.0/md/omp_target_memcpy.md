<!-- source: OpenMP API Specification, section 25.7.1 (omp_target_memcpy Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.7.1 omp_target_memcpy Routine

Name: omp_target_memcpy                                Properties: device-memory-routine,
      Category: function                                     flat-memory-copying, generating-
19
                                                             task-binding, iso_c_binding, memory-
                                                             copying
Return Type and Arguments
      Name                                      Type                        Properties
      <return type>                             c_int                       default
      dst                                       c_ptr                       iso_c, value
      src                                       c_ptr                       intent(in), iso_c, value
length                                    c_size_t                    iso_c, value
      dst_offset                                c_size_t                    iso_c, value
      src_offset                                c_size_t                    iso_c, value
      dst_device_num                            c_int                       iso_c, value
      src_device_num                            c_int                       iso_c, value

Prototypes
                                                C / C++
int omp_target_memcpy(void *dst, const void *src, size_t length,
size_t dst_offset, size_t src_offset, int dst_device_num,
int src_device_num);
                                                C / C++

                                                        Fortran
integer (kind=c_int) function omp_target_memcpy(dst, src, &
length, dst_offset, src_offset, dst_device_num, &
src_device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value :: dst
type (c_ptr), value, intent(in) :: src
integer (kind=c_size_t), value :: length, dst_offset, &
src_offset
integer (kind=c_int), value :: dst_device_num, src_device_num
                                                        Fortran
Effect
As a flat-memory-copying routine, the effect of the omp_target_memcpy routine is as described
in Section 25.7. This effect includes the associated tool events and callbacks defined in that section.

Cross References
• Memory Copying Routines, see Section 25.7
