<!-- source: OpenMP API Specification, section 18.3.5 (omp_get_place_num) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.5 omp_get_place_num

Summary
The omp_get_place_num routine returns the place number of the place to which the
encountering thread is bound.

Format
                                                       C / C++
int omp_get_place_num(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_place_num()
                                                       Fortran

Binding
The binding thread set for an omp_get_place_num region is the encountering thread.

Effect
When the encountering thread is bound to a place, the omp_get_place_num routine returns the
place number associated with the thread. The returned value is between 0 and one less than the
value returned by omp_get_num_places(), inclusive. When the encountering thread is not
bound to a place, the routine returns -1.

Cross References
• omp_get_num_places, see Section 18.3.2
