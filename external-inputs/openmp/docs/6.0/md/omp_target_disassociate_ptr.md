<!-- source: OpenMP API Specification, section 25.6 (omp_target_disassociate_ptr Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.6 omp_target_disassociate_ptr Routine

Name: omp_target_disassociate_ptr                         Properties: device-memory-routine,
 4
      Category: function                                        generating-task-binding, iso_c_binding
Return Type and Arguments
      Name                                        Type                         Properties
      <return type>                               c_int                        default
 6
      ptr                                         c_ptr                        intent(in), iso_c, value
      device_num                                  c_int                        iso_c, value

Prototypes
                                                  C / C++
int omp_target_disassociate_ptr(const void *ptr, int device_num);
                                                  C / C++
                                                  Fortran
integer (kind=c_int) function omp_target_disassociate_ptr(ptr, &
device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr
type (c_ptr), value, intent(in) :: ptr
integer (kind=c_int), value :: device_num
                                                  Fortran
Effect
The omp_target_disassociate_ptr removes the associated device data on device
device_num from the presence table for host pointer ptr. A call to this routine on a pointer that is
not NULL and does not have associated data on the given device results in unspecified behavior.
The reference count of the mapping is reduced to zero, regardless of its current value. The routine
returns zero if successful. Otherwise it returns a non-zero value.

Execution Model Events
The target-data-disassociate event occurs before a thread initiates a device pointer disassociation
on a target device.

Tool Callbacks
A thread dispatches a registered target_data_op_emi callback with
ompt_scope_beginend as its endpoint argument for each occurrence of a
target-data-disassociate event in that thread.

Cross References
• OMPT scope_endpoint Type, see Section 33.27
• target_data_op_emi Callback, see Section 35.7
