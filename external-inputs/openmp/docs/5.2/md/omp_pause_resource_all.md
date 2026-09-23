<!-- source: OpenMP API Specification, section 18.6.2 (omp_pause_resource_all) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.6.2 omp_pause_resource_all

Summary
The omp_pause_resource_all routine allows the runtime to relinquish resources used by
OpenMP on all devices.
Format
                                                         C / C++
int omp_pause_resource_all(omp_pause_resource_t kind);
                                                         C / C++
                                                         Fortran
integer function omp_pause_resource_all(kind)
integer (kind=omp_pause_resource_kind) kind
                                                          Fortran

Binding
The binding task set for an omp_pause_resource_all region is the whole program.
Effect
The omp_pause_resource_all routine allows the runtime to relinquish resources used by
OpenMP on all devices. It is equivalent to calling the omp_pause_resource routine once for
each available device, including the host device.
The argument kind passed to this routine can be one of the valid OpenMP pause kind as defined in
Section 18.6.1, or any implementation-specific pause kind.
Tool Callbacks
If the tool is not allowed to interact with a given device after encountering this call, then the
runtime must call the tool finalizer for that device.
Restrictions
Restrictions to the omp_pause_resource_all routine are as follows:
• The omp_pause_resource_all region may not be nested in any explicit OpenMP region.
• The routine may only be called when all explicit tasks have finalized execution.
Cross References
• omp_pause_resource, see Section 18.6.1
