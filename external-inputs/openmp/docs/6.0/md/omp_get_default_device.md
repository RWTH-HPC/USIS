<!-- source: OpenMP API Specification, section 24.2 (omp_get_default_device Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.2 omp_get_default_device Routine

Name: omp_get_default_device                           Properties: device-information, ICV-
 2
      Category: function                                     retrieving

Return Type
      Name                                        Type                     Properties
 4
      <return type>                               integer                  default

Prototypes
                                                  C / C++
int omp_get_default_device(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_default_device()
                                                  Fortran
Effect
The omp_get_default_device routine returns the value of the default-device-var ICV of the
current task, which is the device number of the default target device. When called from within a
target region the effect of this routine is unspecified.

Cross References
• default-device-var ICV, see Table 3.1
• target Construct, see Section 15.8
