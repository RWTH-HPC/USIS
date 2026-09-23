<!-- source: OpenMP API Specification, section 27.5.6 (omp_mempartition_get_user_data Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.6 omp_mempartition_get_user_data Routine

Name: omp_mempartition_get_user_data                       Properties: all-device-threads-binding,
Category: function                                         iso_c_binding, memory-management-
                                                                 routine, memory-partitioning

Return Type and Arguments
            Name                                       Type                         Properties
            <return type>                              c_ptr                        default
 2
            partition                                  mempartition                 intent(in), C/C++
                                                                                    pointer, omp

Prototypes
                                                      C / C++
void *omp_mempartition_get_user_data(
const omp_mempartition_t *partition);
                                                      C / C++
                                                      Fortran
type (c_ptr) function omp_mempartition_get_user_data(partition) &
bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr
integer (kind=omp_mempartition_kind), intent(in) :: partition
                                                       Fortran
Effect
The effect of the omp_mempartition_get_user_data routine is to retrieve the user data
that was associated with the memory partition when it was created. Thus, the routine returns the
data associated with the memory partition object indicated by the partition argument.
Restrictions
The restrictions to the omp_mempartition_get_user_data routine are as follows:
• The memory partition represented by the partition argument must be in the initialized state.
• This routine must only be called by a procedure that is associated with the memory
partitioner object that allocated the memory partition indicated by the partition argument.
Cross References
• OpenMP Memory Management Types, see Section 20.8
• OpenMP mempartitioner Type, see Section 20.8.7
