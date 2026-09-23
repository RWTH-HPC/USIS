<!-- source: OpenMP API Specification, section 29.4 (omp_get_place_proc_ids Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.4 omp_get_place_proc_ids Routine

Name: omp_get_place_proc_ids                             Properties: all-device-threads-binding,
10
            Category: subroutine                                     ICV-retrieving

Arguments
            Name                                       Type                         Properties
place_num                                  integer                      default
            ids                                        integer                      pointer

Prototypes
                                                       C / C++
void omp_get_place_proc_ids(int place_num, int *ids);
                                                       C / C++
                                                       Fortran
subroutine omp_get_place_proc_ids(place_num, ids)
integer place_num, ids(*)
                                                       Fortran
Effect
The omp_get_place_proc_ids routine returns the numerical identifiers of each processor
associated with the place numbered place_num as per the place-partition-var ICV. The numerical
identifiers are non-negative and their meaning is implementation defined. The numerical identifiers
are returned in the array ids and their order in the array is implementation defined. The array must
be sufficiently large to contain omp_get_place_num_procs(place_num) integers; otherwise,
the behavior is unspecified. The routine has no effect when place_num has a negative value or a
value greater than or equal to omp_get_num_places.

Cross References
• OMP_PLACES, see Section 4.1.6
• omp_get_num_places Routine, see Section 29.2
• omp_get_place_num_procs Routine, see Section 29.3
