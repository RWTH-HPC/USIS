<!-- source: OpenMP API Specification, section 30.2.1 (omp_pause_resource Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.2.1 omp_pause_resource Routine

Name: omp_pause_resource                                   Properties: all-tasks-binding,
14
      Category: function                                         resource-relinquishing
Return Type and Arguments
      Name                                         Type                         Properties
      <return type>                                integer                      default
16
      kind                                         pause_resource               default
      device_num                                   integer                      default

Prototypes
                                                  C / C++
int omp_pause_resource(omp_pause_resource_t kind, int device_num);
                                                  C / C++
                                                  Fortran
integer function omp_pause_resource(kind, device_num)
integer (kind=omp_pause_resource_kind) kind
integer device_num
                                                   Fortran
Effect
The omp_pause_resource routine allows the runtime to relinquish resources used by OpenMP
on the specified device. The device_num argument indicates the device that will be paused. If the
device number has the value omp_invalid_device, runtime error termination is performed.

The binding task set for a omp_pause_resource routine region is all tasks on the specified
device. That is, this routines has the all-device-tasks binding property. If
omp_pause_stop_tool is specified for a non-host device, the effect is the same as for
omp_pause_hard and (unlike for the host device) does not shutdown the OMPT interface.

Restrictions
Restrictions to the omp_pause_resource routine are as follows:
• The device_num argument must be a conforming device number.

Cross References
• Predefined Identifiers, see Section 20.1
• OpenMP pause_resource Type, see Section 20.11.1
