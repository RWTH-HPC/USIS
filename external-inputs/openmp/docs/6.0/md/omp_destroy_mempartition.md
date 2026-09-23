<!-- source: OpenMP API Specification, section 27.5.4 (omp_destroy_mempartition Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.4 omp_destroy_mempartition Routine

Name: omp_destroy_mempartition                            Properties: all-device-threads-
Category: subroutine                                      binding, memory-management-routine,
                                                                memory-partitioning

Arguments
      Name                                       Type                        Properties
partition                                  mempartition                C/C++ pointer, omp,
                                                                             intent(in)

Prototypes
                                                       C / C++
void omp_destroy_mempartition(
const omp_mempartition_t *partition);
                                                       C / C++
                                                       Fortran
subroutine omp_destroy_mempartition(partition)
integer (kind=omp_mempartition_kind), intent(in) :: partition
                                                       Fortran
Effect
The effect of the omp_destroy_mempartition routine is to uninitialize a memory partition
object. Thus, the routine releases the memory partition indicated by the partition argument and all
resources associated with it.

Restrictions
The restrictions to the omp_destroy_mempartition routine are as follows:
• The memory partition represented by the partition argument must be in the initialized state.
• This routine must only be called by a procedure that is associated with the memory
partitioner object that allocated the memory partition indicated by the partition argument.

Cross References
• OpenMP Memory Management Types, see Section 20.8
• OpenMP mempartitioner Type, see Section 20.8.7
