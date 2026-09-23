<!-- source: OpenMP API Specification, section 26.4 (omp_get_interop_str Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.4 omp_get_interop_str Routine

Name: omp_get_interop_str                           Properties: interoperability-property-
20
      Category: function                                  retrieving, interoperability-routine
Return Type and Arguments
      Name                                    Type                      Properties
      <return type>                           const char                pointer
      interop                                 interop                   omp, opaque, intent(in)
22
      property_id                             interop_property          omp
      ret_code                                interop_rc                omp, intent(out), op-
                                                                        tional

Prototypes
                                                    C / C++
const char *omp_get_interop_str(const omp_interop_t interop,
omp_interop_property_t property_id, omp_interop_rc_t *ret_code);
                                                    C / C++
                                                    Fortran
character(:) function omp_get_interop_str(interop, property_id, &
ret_code)
pointer :: omp_get_interop_str
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_property_kind) property_id
integer (kind=omp_interop_rc_kind), intent(out), optional :: &
ret_code
                                                    Fortran
Effect
The omp_get_interop_str routine is an interoperability-property-retrieving routine that
retrieves an interoperability string property type as a string, if available.

Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• OpenMP interop_rc Type, see Section 20.7.4
• omp_get_num_interop_properties Routine, see Section 26.1
