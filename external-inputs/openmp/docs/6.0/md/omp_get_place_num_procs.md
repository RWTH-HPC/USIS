<!-- source: OpenMP API Specification, section 29.3 (omp_get_place_num_procs Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.3 omp_get_place_num_procs Routine

Name: omp_get_place_num_procs                           Properties: all-device-threads-binding,
15
      Category: function                                      ICV-retrieving
Return Type and Arguments
      Name                                      Type                        Properties
<return type>                             integer                     default
      place_num                                 integer                     default

Prototypes
                                                C / C++
int omp_get_place_num_procs(int place_num);
                                                C / C++
                                                Fortran
integer function omp_get_place_num_procs(place_num)
integer place_num
                                                Fortran

Effect
The omp_get_place_num_procs routine returns the number of processors associated with
the place numbered place_num as per the place-partition-var ICV. The routine returns zero when
place_num is negative or is greater than or equal to the value returned by
omp_get_num_places.

Cross References
• place-partition-var ICV, see Table 3.1
• omp_get_num_places Routine, see Section 29.2
