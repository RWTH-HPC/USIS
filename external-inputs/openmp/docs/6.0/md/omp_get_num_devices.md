<!-- source: OpenMP API Specification, section 24.3 (omp_get_num_devices Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.3 omp_get_num_devices Routine

Name: omp_get_num_devices                              Properties: device-information, ICV-
16
      Category: function                                     retrieving

Return Type
      Name                                        Type                     Properties
18
      <return type>                               integer                  default

Prototypes
                                                  C / C++
int omp_get_num_devices(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_num_devices()
                                                  Fortran

Effect
The omp_get_num_devices routine returns the value of the num-devices-var ICV, which is
the number of available non-host devices onto which code or data may be offloaded. When called
from within a target region the effect of this routine is unspecified.

Cross References
• num-devices-var ICV, see Table 3.1
• target Construct, see Section 15.8
