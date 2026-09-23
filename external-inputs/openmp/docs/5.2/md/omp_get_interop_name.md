<!-- source: OpenMP API Specification, section 18.12.5 (omp_get_interop_name) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.5 omp_get_interop_name

Summary
The omp_get_interop_name routine retrieves a property name from an omp_interop_t
object.

Format
const char* omp_get_interop_name(const omp_interop_t interop,
omp_interop_property_t property_id)
;

Effect
The omp_get_interop_name routine returns the name of the property identified by
property_id as a C string. Property names for non-implementation defined properties are listed in
Table 18.1. If the property_id is less than omp_ipr_first or greater than or equal to
omp_get_num_interop_properties(interop), NULL is returned.

Restrictions
Restrictions to the omp_get_interop_name routine are as follows:
• The behavior of the routine is unspecified if an invalid object is provided.
• Memory referenced by the pointer returned by the omp_get_interop_name routine is
managed by the OpenMP implementation and should not be freed or modified.

Cross References
• omp_get_num_interop_properties, see Section 18.12.1
                                                        C / C++

                                                  C / C++
