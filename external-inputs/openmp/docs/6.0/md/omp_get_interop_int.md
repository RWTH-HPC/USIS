<!-- source: OpenMP API Specification, section 26.2 (omp_get_interop_int Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.2 omp_get_interop_int Routine

Name: omp_get_interop_int                                 Properties: interoperability-property-
16
      Category: function                                        retrieving, interoperability-routine
Return Type and Arguments
      Name                                        Type                         Properties
      <return type>                               intptr                       default
      interop                                     interop                      omp, opaque, intent(in)
18
      property_id                                 interop_property             omp
      ret_code                                    interop_rc                   omp, intent(out), op-
                                                                               tional

Prototypes
                                                    C / C++
omp_intptr_t *omp_get_interop_int(const omp_interop_t interop,
omp_interop_property_t property_id, omp_interop_rc_t *ret_code);
                                                    C / C++
                                                    Fortran
integer (kind=c_intptr_t) function omp_get_interop_int(interop, &
property_id, ret_code)
use, intrinsic :: iso_c_binding, only : c_intptr_t
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_property_kind) property_id
integer (kind=omp_interop_rc_kind), intent(out), optional :: &
ret_code
                                                    Fortran
Effect
The omp_get_interop_int routine is an interoperability-property-retrieving routine that
retrieves an interoperability property of integer type, if available.

Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• OpenMP interop_rc Type, see Section 20.7.4
• omp_get_num_interop_properties Routine, see Section 26.1
