<!-- source: OpenMP API Specification, section 30.2.2 (omp_pause_resource_all Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.2.2 omp_pause_resource_all Routine

Name: omp_pause_resource_all                           Properties: all-tasks-binding,
12
            Category: function                                     resource-relinquishing
Return Type and Arguments
            Name                                       Type                      Properties
<return type>                              integer                   default
            kind                                       pause_resource            default

Prototypes
                                                      C / C++
int omp_pause_resource_all(omp_pause_resource_t kind);
                                                      C / C++
                                                      Fortran
integer function omp_pause_resource_all(kind)
integer (kind=omp_pause_resource_kind) kind
                                                       Fortran
Effect
The omp_pause_resource_all routine allows the runtime to relinquish resources used by
OpenMP on all devices. It is equivalent to calling the omp_pause_resource routine once for
each available device, including the host device. The binding task set for a
omp_pause_resource_all routine region is all tasks in the OpenMP program. That is, this
routine has the all-tasks binding property.

Cross References
• omp_pause_resource Routine, see Section 30.2.1
• OpenMP pause_resource Type, see Section 20.11.1
