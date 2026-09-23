<!-- source: OpenMP API Specification, section 26.7 (omp_get_interop_rc_desc Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.7 omp_get_interop_rc_desc Routine

Name: omp_get_interop_rc_desc                            Properties: interoperability-routine
20
            Category: function
Return Type and Arguments
            Name                                        Type                        Properties
            <return type>                               const char                  pointer
22
            interop                                     interop                     omp, opaque, intent(in)
            ret_code                                    interop_rc                  omp

Prototypes
                                                C / C++
const char *omp_get_interop_rc_desc(const omp_interop_t interop,
omp_interop_rc_t ret_code);
                                                C / C++
                                                Fortran
character(:) function omp_get_interop_rc_desc(interop, ret_code)
pointer :: omp_get_interop_rc_desc
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_rc_kind) ret_code
                                                 Fortran
Effect
The omp_get_interop_rc_desc routine returns a string that describes the return code
ret_code associated with an interoperability object in human-readable form.

Restrictions
Restrictions to the omp_get_interop_rc_desc routine are as follows:
• The behavior of the routine is unspecified if ret_code was not last written by an
interoperability routine invoked with the interoperability object interop.

Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• OpenMP interop_rc Type, see Section 20.7.4
• omp_get_num_interop_properties Routine, see Section 26.1
