<!-- source: OpenMP API Specification, section 18.12.2 (omp_get_interop_int) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.12.2 omp_get_interop_int

Summary
The omp_get_interop_int routine retrieves an integer property from an omp_interop_t
object.

Format
omp_intptr_t omp_get_interop_int(const omp_interop_t interop,
omp_interop_property_t property_id,
int *ret_code);

Effect
The omp_get_interop_int routine returns the requested integer property, if available, and
zero if an error occurs or no value is available. If the interop is omp_interop_none, an empty
error occurs. If the property_id is less than omp_ipr_first or greater than or equal to
omp_get_num_interop_properties(interop), an out of range error occurs. If the
requested property value is not convertible into an integer value, a type error occurs.
If a non-null pointer is passed to ret_code, an omp_interop_rc_t value that indicates the
return code is stored in the object to which ret_code points. If an error occurred, the stored value
will be negative and it will match the error as defined in Table 18.2. On success, zero will be stored.
If no error occurred but no meaningful value can be returned, omp_irc_no_value, which is
one, will be stored.

Restrictions
Restrictions to the omp_get_interop_int routine are as follows:
• The behavior of the routine is unspecified if an invalid omp_interop_t object is provided.

Cross References
• omp_get_num_interop_properties, see Section 18.12.1
                                                        C / C++
                                                        C / C++
