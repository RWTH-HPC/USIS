<!-- source: OpenMP API Specification, section 27.5.3 (omp_init_mempartition Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.3 omp_init_mempartition Routine

Name: omp_init_mempartition                                Properties: all-device-threads-binding,
Category: subroutine                                       iso_c_binding, memory-management-
                                                                       routine, memory-partitioning

Arguments
            Name                                        Type                         Properties
            partition                                   mempartition                 C/C++ pointer, omp,
                                                                                     intent(out)
nparts                                      c_size_t                     intent(in), iso_c, in-
                                                                                     tent(in)
            user_data                                   c_ptr                        intent(in), iso_c, in-
                                                                                     tent(in)

Prototypes
                                                C / C++
void omp_init_mempartition(omp_mempartition_t *partition,
size_t nparts, const void *user_data);
                                                C / C++
                                                Fortran
subroutine omp_init_mempartition(partition, nparts, user_data) &
bind(c)
use, intrinsic :: iso_c_binding, only : c_size_t, c_ptr
integer (kind=omp_mempartition_kind), intent(out) :: partition
integer (kind=c_size_t), intent(in) :: nparts
type (c_ptr), intent(in) :: user_data
                                                 Fortran
Effect
The effect of the omp_init_mempartition routine is to initialize a memory partition object.
Thus, the routine sets the memory partition object indicated by the partition argument to represent
a memory partition of nparts parts and associates the user data indicated by the user_data argument
with it.

Restrictions
The restrictions to the omp_init_mempartition routine are as follows:
• The memory partition represented by the partition argument must be in the uninitialized state.
• This routine must only be called by a procedure that is associated with the memory
partitioner object that allocated the memory partition indicated by the partition argument.

Cross References
• OpenMP Memory Management Types, see Section 20.8
• OpenMP mempartitioner Type, see Section 20.8.7
