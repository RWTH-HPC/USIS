<!-- source: OpenMP API Specification, section 24.5 (omp_get_num_procs Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.5 omp_get_num_procs Routine

Name: omp_get_num_procs                                Properties: all-device-threads-binding,
23
            Category: function                                     device-information, ICV-retrieving

Return Type
      Name                                         Type                         Properties
 2
      <return type>                                integer                      default

Prototypes
                                                  C / C++
int omp_get_num_procs(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_num_procs()
                                                   Fortran
Effect
The omp_get_num_procs routine returns the value of the num-procs-var ICV. Thus, this
routine returns the number of processors that are available to the device at the time the routine is
called. This value may change between the time that it is determined by the
omp_get_num_procs routine and the time that it is read in the calling context due to system
actions outside the control of the OpenMP implementation.

Cross References
• num-procs-var ICV, see Table 3.1
