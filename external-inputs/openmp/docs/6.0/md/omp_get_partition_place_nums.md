<!-- source: OpenMP API Specification, section 29.7 (omp_get_partition_place_nums Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.7 omp_get_partition_place_nums Routine

Name: omp_get_partition_place_nums                      Properties: ICV-retrieving
10
            Category: subroutine

Arguments
            Name                                      Type                        Properties
12
            place_nums                                integer                     pointer

Prototypes
                                                      C / C++
void omp_get_partition_place_nums(int *place_nums);
                                                      C / C++
                                                      Fortran
subroutine omp_get_partition_place_nums(place_nums)
integer place_nums(*)
                                                      Fortran
Effect
The omp_get_partition_place_nums routine returns the list of place numbers that
correspond to the places in the place-partition-var ICV of the innermost implicit task. The array
must be sufficiently large to contain omp_get_partition_num_places integers; otherwise,
the behavior is unspecified.

Cross References
• place-partition-var ICV, see Table 3.1
• omp_get_partition_num_places Routine, see Section 29.6
