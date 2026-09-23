<!-- source: OpenMP API Specification, section 18.3.6 (omp_get_partition_num_places) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.6 omp_get_partition_num_places

Summary
The omp_get_partition_num_places routine returns the number of places in the place
partition of the innermost implicit task.

Format
                                                C / C++
int omp_get_partition_num_places(void);
                                                C / C++
                                                Fortran
integer function omp_get_partition_num_places()
                                                Fortran
Binding
The binding task set for an omp_get_partition_num_places region is the encountering
implicit task.

Effect
The omp_get_partition_num_places routine returns the number of places in the
place-partition-var ICV.

Cross References
• place-partition-var ICV, see Table 2.1
