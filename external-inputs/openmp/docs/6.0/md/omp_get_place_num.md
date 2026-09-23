<!-- source: OpenMP API Specification, section 29.5 (omp_get_place_num Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.5 omp_get_place_num Routine

Name: omp_get_place_num                                Properties: default
 6
      Category: function

Return Type
      Name                                      Type                        Properties
 8
      <return type>                             integer                     default

Prototypes
                                                C / C++
int omp_get_place_num(void);
                                                C / C++
                                                Fortran
integer function omp_get_place_num()
                                                Fortran
Effect
When the encountering thread is bound to a place, the omp_get_place_num routine returns the
place number associated with the thread. The returned value is between zero and one less than the
value returned by omp_get_num_places, inclusive. When the encountering thread is not
bound to a place, the routine returns -1.

Cross References
• omp_get_num_places Routine, see Section 29.2
