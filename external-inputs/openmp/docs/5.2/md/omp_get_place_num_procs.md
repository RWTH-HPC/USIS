<!-- source: OpenMP API Specification, section 18.3.3 (omp_get_place_num_procs) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.3 omp_get_place_num_procs

Summary
The omp_get_place_num_procs routine returns the number of processors available to the
execution environment in the specified place.

Format
                                                C / C++
int omp_get_place_num_procs(int place_num);
                                                C / C++
                                                Fortran
integer function omp_get_place_num_procs(place_num)
integer place_num
                                                Fortran
Binding
The binding thread set for an omp_get_place_num_procs region is all threads on a device.
The effect of executing this routine is not related to any specific region corresponding to any
construct or API routine.

Effect
The omp_get_place_num_procs routine returns the number of processors associated with
the place numbered place_num. The routine returns zero when place_num is negative or is greater
than or equal to the value returned by omp_get_num_places().

Cross References
• omp_get_num_places, see Section 18.3.2
