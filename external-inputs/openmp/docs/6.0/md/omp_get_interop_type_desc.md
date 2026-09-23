<!-- source: OpenMP API Specification, section 26.6 (omp_get_interop_type_desc Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.6 omp_get_interop_type_desc Routine

Name: omp_get_interop_type_desc                         Properties: interoperability-routine
18
      Category: function
Return Type and Arguments
      Name                                      Type                        Properties
      <return type>                             const char                  pointer
20
      interop                                   interop                     omp, opaque, intent(in)
      property_id                               interop_property            omp

Prototypes
                                                       C / C++
const char *omp_get_interop_type_desc(
const omp_interop_t interop, omp_interop_property_t property_id);
                                                       C / C++
                                                       Fortran
character(:) function omp_get_interop_type_desc(interop, &
property_id)
pointer :: omp_get_interop_type_desc
integer (kind=omp_interop_kind), intent(in) :: interop
integer (kind=omp_interop_property_kind) property_id
                                                       Fortran
Effect
The omp_get_interop_type_desc routine returns a string that describes the type of the
interoperability property identified by property_id in human-readable form. The description may
contain a valid type declaration, possibly followed by a description or name of the type. If interop
has the value omp_interop_none, or if the property_id is less than omp_ipr_first or
greater than or equal to omp_get_num_interop_properties(interop), NULL is returned.

Cross References
• OpenMP interop Type, see Section 20.7.1
• OpenMP interop_property Type, see Section 20.7.3
• omp_get_num_interop_properties Routine, see Section 26.1
