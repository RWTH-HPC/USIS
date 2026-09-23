<!-- source: OpenMP API Specification, section 25.8.1 (omp_target_memset Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.8.1 omp_target_memset Routine

Name: omp_target_memset                                  Properties: device-memory-routine,
Category: function                                       generating-task-binding, iso_c_bind-
                                                               ing, memory-setting
Return Type and Arguments
      Name                                        Type                       Properties
      <return type>                               c_ptr                      default
      ptr                                         c_ptr                      iso_c, value
17
      val                                         c_int                      iso_c, value
      count                                       c_size_t                   iso_c, value
      device_num                                  c_int                      iso_c, value

Prototypes
                                                 C / C++
void *omp_target_memset(void *ptr, int val, size_t count,
int device_num);
                                                 C / C++
                                                 Fortran
type (c_ptr) function omp_target_memset(ptr, val, count, &
device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int, &
c_size_t
type (c_ptr), value :: ptr
integer (kind=c_int), value :: val, device_num
integer (kind=c_size_t), value :: count
                                                  Fortran

Effect
As a memory-setting routine, the effect of the omp_target_memset routine is as described in
Section 25.8. This effect includes the tool events and callbacks defined in that section.

Cross References
• Memory Setting Routines, see Section 25.8
