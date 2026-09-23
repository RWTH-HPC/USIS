<!-- source: OpenMP API Specification, section 25.4 (omp_target_free Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.4 omp_target_free Routine

Name: omp_target_free                                     Properties: device-memory-routine,
10
            Category: subroutine                                      generating-task-binding, iso_c_binding

Arguments
            Name                                        Type                         Properties
device_ptr                                  c_ptr                        iso_c, value
            device_num                                  c_int                        iso_c, value

Prototypes
                                                        C / C++
void omp_target_free(void *device_ptr, int device_num);
                                                        C / C++
                                                        Fortran
subroutine omp_target_free(device_ptr, device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_int
type (c_ptr), value :: device_ptr
integer (kind=c_int), value :: device_num
                                                        Fortran
Effect
The omp_target_free routine frees the memory in the device data environment associated
with device_ptr. If device_ptr is NULL, the operation is ignored.

Execution Model Events
The target-data-free-begin event occurs before a thread initiates a data free on a target device. The
target-data-free-end event occurs after a thread initiates a data free on a target device.

Tool Callbacks
A thread dispatches a registered target_data_op_emi callback with ompt_scope_begin
as its endpoint argument for each occurrence of a target-data-free-begin event in that thread.
Similarly, a thread dispatches a registered target_data_op_emi callback with
ompt_scope_end as its endpoint argument for each occurrence of a target-data-free-end event
in that thread.
Restrictions
Restrictions to the omp_target_free routine are as follows:
• The value of device_ptr must be NULL or have been returned by omp_target_alloc.
Cross References
• omp_target_alloc Routine, see Section 25.3
• OMPT scope_endpoint Type, see Section 33.27
• target_data_op_emi Callback, see Section 35.7
