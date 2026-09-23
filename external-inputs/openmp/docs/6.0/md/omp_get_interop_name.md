<!-- source: OpenMP API Specification, section 26.5 (omp_get_interop_name Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.5 omp_get_interop_name Routine

Name: omp_get_interop_name                          Properties: interoperability-routine
20
            Category: function
Return Type and Arguments
            Name                                    Type                      Properties
            <return type>                           const char                pointer
22
            interop                                 interop                   omp, opaque, intent(in)
            property_id                             interop_property          omp

Prototypes
                                                C / C++
const char *omp_get_interop_name(const omp_interop_t interop,
omp_interop_property_t property_id);
                                                C / C++
                                                Fortran
character(:) function omp_get_interop_name(interop, property_id)
pointer :: omp_get_interop_name
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_property_kind) property_id
                                                Fortran
Effect
The omp_get_interop_name routine returns, as a string, the name of the interoperability
property identified by property_id. Property names for non-implementation defined interoperability
properties are listed in Table 20.2. If the property_id is less than omp_ipr_first or greater than
or equal to omp_get_num_interop_properties(interop), NULL is returned.
Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• omp_get_num_interop_properties Routine, see Section 26.1
