<!-- source: OpenMP API Specification, section 18.12.3 (omp_get_interop_ptr) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.3 omp_get_interop_ptr

Summary
The omp_get_interop_ptr routine retrieves a pointer property from an omp_interop_t
object.

Format
void* omp_get_interop_ptr(const omp_interop_t interop,
omp_interop_property_t property_id,
int *ret_code);

Effect
The omp_get_interop_ptr routine returns the requested pointer property, if available, and
NULL if an error occurs or no value is available. If the interop is omp_interop_none, an empty
error occurs. If the property_id is less than omp_ipr_first or greater than or equal to
omp_get_num_interop_properties(interop), an out of range error occurs. If the
requested property value is not convertible into a pointer value, a type error occurs.

If a non-null pointer is passed to ret_code, an omp_interop_rc_t value that indicates the
return code is stored in the object to which the ret_code points. If an error occurred, the stored
value will be negative and it will match the error as defined in Table 18.2. On success, zero will be
stored. If no error occurred but no meaningful value can be returned, omp_irc_no_value,
which is one, will be stored.

Restrictions
Restrictions to the omp_get_interop_ptr routine are as follows:
• The behavior of the routine is unspecified if an invalid omp_interop_t object is provided.
• Memory referenced by the pointer returned by the omp_get_interop_ptr routine is
managed by the OpenMP implementation and should not be freed or modified.

Cross References
• omp_get_num_interop_properties, see Section 18.12.1
                                                  C / C++

                                                  C / C++
