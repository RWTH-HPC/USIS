<!-- source: OpenMP API Specification, section 25.7.4 (omp_target_memcpy_rect_async Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.7.4 omp_target_memcpy_rect_async Routine

Name: omp_target_memcpy_rect_async                Properties: asynchronous-device-
      Category: function                                routine, device-memory-routine,
generating-task-binding, iso_c_bind-
                                                        ing, memory-copying, rectangular-
                                                        memory-copying
Return Type and Arguments
      Name                                 Type                       Properties
      <return type>                        c_int                      default
      dst                                  c_ptr                      iso_c, value
      src                                  c_ptr                      intent(in), iso_c, value
      element_size                         c_size_t                   iso_c, value
      num_dims                             c_int                      iso_c, positive, value
      volume                               c_size_t                   intent(in), iso_c, pointer
dst_offsets                          c_size_t                   intent(in), iso_c, pointer
      src_offsets                          c_size_t                   intent(in), iso_c, pointer
      dst_dimensions                       c_size_t                   intent(in), iso_c, pointer
      src_dimensions                       c_size_t                   intent(in), iso_c, pointer
      dst_device_num                       c_int                      iso_c, value
      src_device_num                       c_int                      iso_c, value
      depobj_count                         c_int                      iso_c, value
      depobj_list                          depend                     optional, pointer

Prototypes
                                           C / C++
int omp_target_memcpy_rect_async(void *dst, const void *src,
size_t element_size, int num_dims, const size_t *volume,
const size_t *dst_offsets, const size_t *src_offsets,
const size_t *dst_dimensions, const size_t *src_dimensions,
int dst_device_num, int src_device_num, int depobj_count,
omp_depend_t *depobj_list);
                                           C / C++

                                                         Fortran
integer (kind=c_int) function omp_target_memcpy_rect_async(dst, &
src, element_size, num_dims, volume, dst_offsets, src_offsets, &
dst_dimensions, src_dimensions, dst_device_num, &
src_device_num, depobj_count, depobj_list) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value :: dst
type (c_ptr), value, intent(in) :: src
integer (kind=c_size_t), value :: element_size
integer (kind=c_int), value :: num_dims, dst_device_num, &
src_device_num, depobj_count
integer (kind=c_size_t), intent(in) :: volume(*), dst_offsets&
(*), src_offsets(*), dst_dimensions(*), src_dimensions(*)
integer (kind=omp_depend_kind), optional :: depobj_list(*)
                                                         Fortran
Effect
As a rectangular-memory-copying routine, the effect of the
omp_target_memcpy_rect_async routine is as described in Section 25.7. This effect
includes the tool events and callbacks defined in that section. As it is also an asynchronous device
routine, the routine also includes the tool events and callbacks defined in Section 25.1.

Cross References
• Asynchronous Device Memory Routines, see Section 25.1
• Memory Copying Routines, see Section 25.7
