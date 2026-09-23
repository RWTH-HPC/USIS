<!-- source: OpenMP API Specification, section 18.3.2 (omp_get_num_places) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.2 omp_get_num_places

Summary
The omp_get_num_places routine returns the number of places available to the execution
environment in the place list.

Format
                                                         C / C++
int omp_get_num_places(void);
                                                         C / C++
                                                         Fortran
integer function omp_get_num_places()
                                                         Fortran
Binding
The binding thread set for an omp_get_num_places region is all threads on a device. The
effect of executing this routine is not related to any specific region corresponding to any construct
or API routine.

Effect
The omp_get_num_places routine returns the number of places in the place list. This value is
equivalent to the number of places in the place-partition-var ICV in the execution environment of
the initial task.

Cross References
• place-partition-var ICV, see Table 2.1
