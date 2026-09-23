<!-- source: OpenMP API Specification, section 18.12.7 (omp_get_interop_rc_desc) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.7 omp_get_interop_rc_desc

Summary
The omp_get_interop_rc_desc routine retrieves a description of the return code associated
with an omp_interop_t object.

Format
const char* omp_get_interop_rc_desc(const omp_interop_t interop,
omp_interop_rc_t ret_code);

Effect
The omp_get_interop_rc_desc routine returns a C string that describes the return code
ret_code in human-readable form.

Restrictions
Restrictions to the omp_get_interop_rc_desc routine are as follows:
• The behavior of the routine is unspecified if an invalid object is provided or if ret_code was not
last written by an interoperability routine invoked with the omp_interop_t object interop.
• Memory referenced by the pointer returned by the omp_get_interop_rc_desc routine is
managed by the OpenMP implementation and should not be freed or modified.
                                                        C / C++
