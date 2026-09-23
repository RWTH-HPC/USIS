<!-- source: OpenMP API Specification, section 25.3 (omp_target_alloc Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.3 omp_target_alloc Routine

Name: omp_target_alloc                                   Properties: device-memory-routine,
25
            Category: function                                       generating-task-binding, iso_c_binding

Return Type and Arguments
      Name                                        Type                         Properties
      <return type>                               c_ptr                        default
 2
      size                                        c_size_t                     iso_c, value
      device_num                                  c_int                        iso_c, value

Prototypes
                                                  C / C++
void     *omp_target_alloc(size_t size, int device_num);
                                                  C / C++
                                                  Fortran
type (c_ptr) function omp_target_alloc(size, device_num) &
bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t, &
c_int
integer (kind=c_size_t), value :: size
integer (kind=c_int), value :: device_num
                                                  Fortran
Effect
The omp_target_alloc routine returns a device pointer that references the device address of a
storage location of size bytes. The storage location is dynamically allocated in the device data
environment of the device specified by device_num.
The omp_target_alloc routine returns NULL if it cannot dynamically allocate the memory in
the device data environment or if size is 0. The device pointer returned by omp_target_alloc
can be used in an is_device_ptr clause (see Section 7.5.7).

Execution Model Events
The target-data-allocation-begin event occurs before a thread initiates a data allocation on a target
device. The target-data-allocation-end event occurs after a thread initiates a data allocation on a
target device.

Tool Callbacks
A thread dispatches a registered target_data_op_emi callback with ompt_scope_begin
as its endpoint argument for each occurrence of a target-data-allocation-begin event in that thread.
Similarly, a thread dispatches a registered target_data_op_emi callback with
ompt_scope_end as its endpoint argument for each occurrence of a target-data-allocation-end
event in that thread.

Restrictions
Restrictions to the omp_target_alloc routine are as follows:
• Freeing the storage returned by omp_target_alloc with any routine other than
omp_target_free results in unspecified behavior.

                                                        C / C++
• Unless the unified_address clause appears on a requires directive in the
compilation unit, pointer arithmetic is not supported on the device pointer returned by
omp_target_alloc.
                                                        C / C++
Cross References
• is_device_ptr Clause, see Section 7.5.7
• omp_target_free Routine, see Section 25.4
• OMPT scope_endpoint Type, see Section 33.27
• target_data_op_emi Callback, see Section 35.7
