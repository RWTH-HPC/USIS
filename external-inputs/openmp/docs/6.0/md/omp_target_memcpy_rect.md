<!-- source: OpenMP API Specification, section 25.7.2 (omp_target_memcpy_rect Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.7.2 omp_target_memcpy_rect Routine

Name: omp_target_memcpy_rect                               Properties: device-memory-routine,
            Category: function                                         generating-task-binding, iso_c_bind-
17
                                                                       ing, memory-copying, rectangular-
                                                                       memory-copying
Return Type and Arguments
            Name                                         Type                         Properties
            <return type>                                c_int                        default
            dst                                          c_ptr                        iso_c, value
            src                                          c_ptr                        intent(in), iso_c, value
            element_size                                 c_size_t                     iso_c, value
            num_dims                                     c_int                        iso_c, positive, value
volume                                       c_size_t                     intent(in), iso_c, pointer
            dst_offsets                                  c_size_t                     intent(in), iso_c, pointer
            src_offsets                                  c_size_t                     intent(in), iso_c, pointer
            dst_dimensions                               c_size_t                     intent(in), iso_c, pointer
            src_dimensions                               c_size_t                     intent(in), iso_c, pointer
            dst_device_num                               c_int                        iso_c, value
            src_device_num                               c_int                        iso_c, value

Prototypes
                                                  C / C++
int omp_target_memcpy_rect(void *dst, const void *src,
size_t element_size, int num_dims, const size_t *volume,
const size_t *dst_offsets, const size_t *src_offsets,
const size_t *dst_dimensions, const size_t *src_dimensions,
int dst_device_num, int src_device_num);
                                                  C / C++
                                                  Fortran
integer (kind=c_int) function omp_target_memcpy_rect(dst, src, &
element_size, num_dims, volume, dst_offsets, src_offsets, &
dst_dimensions, src_dimensions, dst_device_num, &
src_device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value :: dst
type (c_ptr), value, intent(in) :: src
integer (kind=c_size_t), value :: element_size
integer (kind=c_int), value :: num_dims, dst_device_num, &
src_device_num
integer (kind=c_size_t), intent(in) :: volume(*), dst_offsets&
(*), src_offsets(*), dst_dimensions(*), src_dimensions(*)
                                                  Fortran
Effect
As a rectangular-memory-copying routine, the effect of the omp_target_memcpy_rect
routine is as described in Section 25.7. This effect includes the associated tool events and callbacks
defined in that section.

Cross References
• Memory Copying Routines, see Section 25.7
