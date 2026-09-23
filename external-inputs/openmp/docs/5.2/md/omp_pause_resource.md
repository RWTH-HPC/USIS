<!-- source: OpenMP API Specification, section 18.6.1 (omp_pause_resource) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.6.1 omp_pause_resource

Summary
The omp_pause_resource routine allows the runtime to relinquish resources used by OpenMP
on the specified device.
Format
                                                      C / C++
int omp_pause_resource(omp_pause_resource_t kind, int device_num);
                                                      C / C++

                                                Fortran
integer function omp_pause_resource(kind, device_num)
integer (kind=omp_pause_resource_kind) kind
integer device_num
                                                Fortran
Constraints on Arguments
The first argument passed to this routine can be one of the valid OpenMP pause kind, or any
implementation-specific pause kind. The C/C++ header file (omp.h) and the Fortran include file
(omp_lib.h) and/or Fortran module file (omp_lib) define the valid constants. The valid
constants must include the following, which can be extended with implementation-specific values:
                                                C / C++
typedef enum omp_pause_resource_t {
omp_pause_soft = 1,
omp_pause_hard = 2
} omp_pause_resource_t;
                                                C / C++
                                                Fortran
integer (kind=omp_pause_resource_kind), parameter :: &
omp_pause_soft = 1
integer (kind=omp_pause_resource_kind), parameter :: &
omp_pause_hard = 2
                                                Fortran
The second argument passed to this routine indicates the device that will be paused. The
device_num parameter must be a conforming device number. If the device number has the value
omp_invalid_device, runtime error termination is performed.

Binding
The binding task set for an omp_pause_resource region is the whole program.

Effect
The omp_pause_resource routine allows the runtime to relinquish resources used by OpenMP
on the specified device.
If successful, the omp_pause_hard value results in a hard pause for which the OpenMP state is
not guaranteed to persist across the omp_pause_resource call. A hard pause may relinquish
any data allocated by OpenMP on a given device, including data allocated by memory routines for
that device as well as data present on the device as a result of a declare target directive or
target data construct. A hard pause may also relinquish any data associated with a
threadprivate directive. When relinquished and when applicable, base language appropriate
deallocation/finalization is performed. When relinquished and when applicable, mapped data on a
device will not be copied back from the device to the host.

If successful, the omp_pause_soft value results in a soft pause for which the OpenMP state is
guaranteed to persist across the call, with the exception of any data associated with a
threadprivate directive, which may be relinquished across the call. When relinquished and
when applicable, base language appropriate deallocation/finalization is performed.
 5

Note – A hard pause may relinquish more resources, but may resume processing OpenMP regions
more slowly. A soft pause allows OpenMP regions to restart more quickly, but may relinquish fewer
resources. An OpenMP implementation will reclaim resources as needed for OpenMP regions
encountered after the omp_pause_resource region. Since a hard pause may unmap data on the
specified device, appropriate data mapping is required before using data on the specified device
after the omp_pause_region region.
12
The routine returns zero in case of success, and non-zero otherwise.
Tool Callbacks
If the tool is not allowed to interact with the specified device after encountering this call, then the
runtime must call the tool finalizer for that device.
Restrictions
Restrictions to the omp_pause_resource routine are as follows:
• The omp_pause_resource region may not be nested in any explicit OpenMP region.
• The routine may only be called when all explicit tasks have finalized execution.
Cross References
• Declare Target Directives, see Section 7.8
• target data directive, see Section 13.5
• threadprivate directive, see Section 5.2
