<!-- source: OpenMP API Specification, section 25.7.3 (omp_target_memcpy_async Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.7.3 omp_target_memcpy_async Routine

Name: omp_target_memcpy_async                             Properties: asynchronous-device-
      Category: function                                        routine, device-memory-routine, flat-
memory-copying, generating-task-
                                                                binding, iso_c_binding, memory-
                                                                copying

Return Type and Arguments
            Name                                        Type                          Properties
            <return type>                               c_int                         default
            dst                                         c_ptr                         iso_c, value
            src                                         c_ptr                         intent(in), iso_c, value
            length                                      c_size_t                      iso_c, value
dst_offset                                  c_size_t                      iso_c, value
            src_offset                                  c_size_t                      iso_c, value
            dst_device_num                              c_int                         iso_c, value
            src_device_num                              c_int                         iso_c, value
            depobj_count                                c_int                         iso_c, value
            depobj_list                                 depend                        optional, pointer

Prototypes
                                                        C / C++
int omp_target_memcpy_async(void *dst, const void *src,
size_t length, size_t dst_offset, size_t src_offset,
int dst_device_num, int src_device_num, int depobj_count,
omp_depend_t *depobj_list);
                                                        C / C++
                                                        Fortran
integer (kind=c_int) function omp_target_memcpy_async(dst, src, &
length, dst_offset, src_offset, dst_device_num, &
src_device_num, depobj_count, depobj_list) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value :: dst
type (c_ptr), value, intent(in) :: src
integer (kind=c_size_t), value :: length, dst_offset, &
src_offset
integer (kind=c_int), value :: dst_device_num, src_device_num, &
depobj_count
integer (kind=omp_depend_kind), optional :: depobj_list(*)
                                                        Fortran
Effect
As a flat-memory-copying routine, the effect of the omp_target_memcpy_async routine is as
described in Section 25.7. This effect includes the tool events and callbacks defined in that section.
As it is also an asynchronous device routine, the routine also includes the tool events and callbacks
defined in Section 25.1.

Cross References
• Asynchronous Device Memory Routines, see Section 25.1
• Memory Copying Routines, see Section 25.7
