<!-- source: OpenMP API Specification, section 26.3 (omp_get_interop_ptr Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.3 omp_get_interop_ptr Routine

Name: omp_get_interop_ptr                           Properties: interoperability-property-
20
            Category: function                                  retrieving, interoperability-routine
Return Type and Arguments
            Name                                    Type                      Properties
            <return type>                           c_ptr                     default
            interop                                 interop                   omp, opaque, intent(in)
22
            property_id                             interop_property          omp
            ret_code                                interop_rc                omp, intent(out), op-
                                                                              tional

Prototypes
                                             C / C++
void *omp_get_interop_ptr(const omp_interop_t interop,
omp_interop_property_t property_id, omp_interop_rc_t *ret_code);
                                             C / C++
                                             Fortran
type (c_ptr) function omp_get_interop_ptr(interop, property_id, &
ret_code)
use, intrinsic :: iso_c_binding, only : c_ptr
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_property_kind) property_id
integer (kind=omp_interop_rc_kind), intent(out), optional :: &
ret_code
                                              Fortran
Effect
The omp_get_interop_ptr routine is an interoperability-property-retrieving routine that
retrieves an interoperability property of pointer type, if available.

Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• OpenMP interop_rc Type, see Section 20.7.4
• omp_get_num_interop_properties Routine, see Section 26.1
