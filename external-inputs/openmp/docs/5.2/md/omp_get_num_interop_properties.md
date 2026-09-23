<!-- source: OpenMP API Specification, section 18.12.1 (omp_get_num_interop_properties) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.1 omp_get_num_interop_properties

Summary
The omp_get_num_interop_properties routine retrieves the number of
implementation-defined properties available for an omp_interop_t object.

Format
int omp_get_num_interop_properties(const omp_interop_t interop);

Effect
The omp_get_num_interop_properties routine returns the number of
implementation-defined properties available for interop. The total number of properties available
for interop is the returned value minus omp_ipr_first.
                                                   C / C++

                                                   C / C++
