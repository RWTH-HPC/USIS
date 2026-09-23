<!-- source: OpenMP API Specification, section 25.8.2 (omp_target_memset_async Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.8.2 omp_target_memset_async Routine

Name: omp_target_memset_async                        Properties: asynchronous-device-
            Category: function                                   routine, device-memory-routine,
 7
                                                                 generating-task-binding, iso_c_bind-
                                                                 ing, memory-setting
Return Type and Arguments
            Name                                    Type                       Properties
            <return type>                           c_ptr                      default
            ptr                                     c_ptr                      iso_c, value
            val                                     c_int                      iso_c, value
 9
            count                                   c_size_t                   iso_c, value
            device_num                              c_int                      iso_c, value
            depobj_count                            c_int                      iso_c, value
            depobj_list                             depend                     optional, pointer

Prototypes
                                                    C / C++
void *omp_target_memset_async(void *ptr, int val, size_t count,
int device_num, int depobj_count, omp_depend_t *depobj_list);
                                                    C / C++
                                                    Fortran
type (c_ptr) function omp_target_memset_async(ptr, val, count, &
device_num, depobj_count, depobj_list) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int, &
c_size_t
type (c_ptr), value :: ptr
integer (kind=c_int), value :: val, device_num, depobj_count
integer (kind=c_size_t), value :: count
integer (kind=omp_depend_kind), optional :: depobj_list(*)
                                                    Fortran

Effect
As a memory-setting routine, the effect of the omp_target_memset_async routine is as
described in Section 25.8. This effect includes the tool events and callbacks defined in that section.
As it is also an asynchronous device routine, the routine also includes the tool events and callbacks
defined in Section 25.1.

Cross References
• Asynchronous Device Memory Routines, see Section 25.1
• Memory Setting Routines, see Section 25.8
