<!-- source: OpenMP API Specification, section 18.3.4 (omp_get_place_proc_ids) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.4 omp_get_place_proc_ids

Summary
The omp_get_place_proc_ids routine returns the numerical identifiers of the processors
available to the execution environment in the specified place.

Format
                                                       C / C++
void omp_get_place_proc_ids(int place_num, int *ids);
                                                       C / C++
                                                       Fortran
subroutine omp_get_place_proc_ids(place_num, ids)
integer place_num
integer ids(*)
                                                       Fortran
Binding
The binding thread set for an omp_get_place_proc_ids region is all threads on a device.
The effect of executing this routine is not related to any specific region corresponding to any
construct or API routine.

Effect
The omp_get_place_proc_ids routine returns the numerical identifiers of each processor
associated with the place numbered place_num. The numerical identifiers are non-negative and
their meaning is implementation defined. The numerical identifiers are returned in the array ids and
their order in the array is implementation defined. The array must be sufficiently large to contain
omp_get_place_num_procs(place_num) integers; otherwise, the behavior is unspecified.
The routine has no effect when place_num has a negative value or a value greater than or equal to
omp_get_num_places().

Cross References
• OMP_PLACES, see Section 21.1.6
• omp_get_num_places, see Section 18.3.2
• omp_get_place_num_procs, see Section 18.3.3
