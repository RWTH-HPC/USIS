<!-- source: OpenMP API Specification, section 18.3.7 (omp_get_partition_place_nums) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.7 omp_get_partition_place_nums

Summary
The omp_get_partition_place_nums routine returns the list of place numbers
corresponding to the places in the place-partition-var ICV of the innermost implicit task.

Format
                                                       C / C++
void omp_get_partition_place_nums(int *place_nums);
                                                       C / C++
                                                       Fortran
subroutine omp_get_partition_place_nums(place_nums)
integer place_nums(*)
                                                       Fortran
Binding
The binding task set for an omp_get_partition_place_nums region is the encountering
implicit task.

Effect
The omp_get_partition_place_nums routine returns the list of place numbers that
correspond to the places in the place-partition-var ICV of the innermost implicit task. The array
must be sufficiently large to contain omp_get_partition_num_places() integers;
otherwise, the behavior is unspecified.

Cross References
• omp_get_partition_num_places, see Section 18.3.6
• place-partition-var ICV, see Table 2.1
