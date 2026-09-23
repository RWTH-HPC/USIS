<!-- source: OpenMP API Specification, section 26.1 (omp_get_num_interop_properties Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 26 Interoperability Routines -->

# 26.1 omp_get_num_interop_properties Routine

Name: omp_get_num_interop_properties                      Properties: interoperability-routine
 2
      Category: function
Return Type and Arguments
      Name                                        Type                         Properties
<return type>                               integer                      default
      interop                                     interop                      intent(in)

Prototypes
                                                  C / C++
int omp_get_num_interop_properties(const omp_interop_t interop);
                                                  C / C++
                                                  Fortran
integer function omp_get_num_interop_properties(interop)
integer (kind=omp_interop_kind), intent(in) :: interop
                                                  Fortran
Effect
The omp_get_num_interop_properties routine returns the number of implementation
defined interoperability properties available for interop. The total number of properties available
for interop is the returned value minus omp_ipr_first.

Cross References
• OpenMP interop Type, see Section 20.7.1
