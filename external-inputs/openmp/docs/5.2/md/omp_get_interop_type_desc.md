<!-- source: OpenMP API Specification, section 18.12.6 (omp_get_interop_type_desc) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.6 omp_get_interop_type_desc

Summary
The omp_get_interop_type_desc routine retrieves a description of the type of a property
associated with an omp_interop_t object.

Format
const char* omp_get_interop_type_desc(const omp_interop_t interop,
omp_interop_property_t
property_id);

Effect
The omp_get_interop_type_desc routine returns a C string that describes the type of the
property identified by property_id in human-readable form. That may contain a valid C type
declaration possibly followed by a description or name of the type. If interop has the value
omp_interop_none, NULL is returned. If the property_id is less than omp_ipr_first or
greater than or equal to omp_get_num_interop_properties(interop), NULL is returned.

Restrictions
Restrictions to the omp_get_interop_type_desc routine are as follows:
• The behavior of the routine is unspecified if an invalid object is provided.
• Memory referenced by the pointer returned from the omp_get_interop_type_desc
routine is managed by the OpenMP implementation and should not be freed or modified.

Cross References
• omp_get_num_interop_properties, see Section 18.12.1
                                                  C / C++
                                                  C / C++
