<!-- source: OpenMP API Specification, section 29.6 (omp_get_partition_num_places Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.6 omp_get_partition_num_places Routine

Name: omp_get_partition_num_places                     Properties: ICV-retrieving
20
      Category: function

Return Type
      Name                                      Type                        Properties
22
      <return type>                             integer                     default

Prototypes
                                                      C / C++
int omp_get_partition_num_places(void);
                                                      C / C++
                                                      Fortran
integer function omp_get_partition_num_places()
                                                      Fortran
Effect
The omp_get_partition_num_places routine returns the number of places in the
place-partition-var ICV.

Cross References
• place-partition-var ICV, see Table 3.1
