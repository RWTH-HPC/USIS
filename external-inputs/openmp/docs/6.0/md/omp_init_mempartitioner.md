<!-- source: OpenMP API Specification, section 27.5.1 (omp_init_mempartitioner Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.1 omp_init_mempartitioner Routine

Name: omp_init_mempartitioner                           Properties: all-device-threads-
Category: subroutine                                    binding, memory-management-routine,
                                                                    memory-partitioning

Arguments
            Name                                      Type                        Properties
            partitioner                               mempartitioner              C/C++ pointer, omp,
                                                                                  intent(out)
            lifetime                                  mempartitioner_lifetime     omp, intent(in)
 4
            compute_proc                              mempartitioner_com-         omp, procedure
                                                      pute_proc
            release_proc                              mempartitioner_re-          omp, procedure
                                                      lease_proc

Prototypes
                                                      C / C++
void omp_init_mempartitioner(omp_mempartitioner_t *partitioner,
omp_mempartitioner_lifetime_t lifetime,
omp_mempartitioner_compute_proc_t compute_proc,
omp_mempartitioner_release_proc_t release_proc);
                                                      C / C++
                                                      Fortran
subroutine omp_init_mempartitioner(partitioner, lifetime, &
compute_proc, release_proc)
integer (kind=omp_mempartitioner_kind), intent(out) :: &
partitioner
integer (kind=omp_mempartitioner_lifetime_kind), &
intent(in) :: lifetime
procedure (omp_mempartitioner_compute_proc_t) compute_proc
procedure (omp_mempartitioner_release_proc_t) release_proc
                                                      Fortran
Effect
The omp_init_mempartitioner routine initializes the memory partitioner that the
partitioner object represents with the lifetime specified by the lifetime argument, and the
compute_proc partition computation procedure and the release_proc partition release procedure.
Once initialized the partitioner object can be associated with an allocator when the allocator is
initialized with omp_init_allocator by using the omp_atk_partitioner trait. If the
omp_atk_partition allocator trait is set to omp_atv_partitioner, then, for allocations

that use the allocator, the number of memory parts of an allocation and how they are distributed
across the storage resources are defined by a memory partition object that must be initialized in the
compute_proc provided in this routine through calls to the omp_init_mempartition and
omp_mempartition_set_part routines.
If the value of the lifetime argument is omp_allocator_mempartition then the memory
partition object that is created through the compute_proc procedure might be used for all
allocations of an allocator that has the same allocation size. If the value of the lifetime argument is
omp_dynamic_mempartition then a memory partition object will be initialized for every
allocation.

Restrictions
The restrictions to the omp_init_mempartitioner routine are as follows:
• The memory partitioner represented by the partitioner argument must be in the uninitialized
state.

Cross References
• Memory Allocators, see Section 8.2
• Memory Spaces, see Section 8.1
• OpenMP mempartitioner Type, see Section 20.8.7
• OpenMP mempartitioner_compute_proc Type, see Section 20.8.9
• OpenMP mempartitioner_lifetime Type, see Section 20.8.8
• OpenMP mempartitioner_release_proc Type, see Section 20.8.10
