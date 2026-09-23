<!-- source: OpenMP API Specification, section 27.5.2 (omp_destroy_mempartitioner Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.2 omp_destroy_mempartitioner Routine

Name: omp_destroy_mempartitioner                           Properties: all-device-threads-
Category: subroutine                                       binding, memory-management-routine,
                                                                 memory-partitioning

Arguments
      Name                                         Type                          Properties
partitioner                                  mempartitioner                C/C++ pointer, omp,
                                                                                 intent(in)

Prototypes
                                                   C / C++
void omp_destroy_mempartitioner(
const omp_mempartitioner_t *partitioner);
                                                   C / C++

                                                        Fortran
subroutine omp_destroy_mempartitioner(partitioner)
integer (kind=omp_mempartitioner_kind), intent(in) :: &
partitioner
                                                        Fortran
Effect
The effect of the omp_destroy_mempartitioner routine is to uninitialize a memory
partitioner. Thus, the routine changes the state of the memory partitioner object represented by the
partitioner argument to uninitialized and releases all resources associated with it.

Restrictions
The restrictions to the omp_destroy_mempartitioner routine are as follows:
• The memory partitioner represented by the partitioner argument must be in the initialized
state.
• Any allocator that references the memory partitioner object represented by the partitioner
argument must be destroyed before this routine is called.

Cross References
• Memory Allocators, see Section 8.2
• OpenMP mempartitioner Type, see Section 20.8.7
