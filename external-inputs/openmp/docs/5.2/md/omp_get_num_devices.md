<!-- source: OpenMP API Specification, section 18.7.4 (omp_get_num_devices) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.7.4 omp_get_num_devices

Summary
The omp_get_num_devices routine returns the number of non-host devices available for
offloading code or data.

Format
                                               C / C++
int omp_get_num_devices(void);
                                               C / C++
                                               Fortran
integer function omp_get_num_devices()
                                               Fortran
Binding
The binding task set for an omp_get_num_devices region is the generating task.

Effect
The omp_get_num_devices routine returns the number of available non-host devices onto
which code or data may be offloaded. When called from within a target region the effect of this
routine is unspecified.

Cross References
• target directive, see Section 13.8
