<!-- source: OpenMP API Specification, section 25.5 (omp_target_associate_ptr Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 25 Device Memory Routines -->

# 25.5 omp_target_associate_ptr Routine

Name: omp_target_associate_ptr                        Properties: device-memory-routine,
15
      Category: function                                    generating-task-binding, iso_c_binding
Return Type and Arguments
      Name                                     Type                       Properties
      <return type>                            c_int                      default
      host_ptr                                 c_ptr                      intent(in), iso_c, value
device_ptr                               c_ptr                      intent(in), iso_c, value
      size                                     c_size_t                   iso_c, value
      device_offset                            c_size_t                   iso_c, value
      device_num                               c_int                      iso_c, value

Prototypes
                                               C / C++
int omp_target_associate_ptr(const void *host_ptr,
const void *device_ptr, size_t size, size_t device_offset,
int device_num);
                                               C / C++

                                                        Fortran
integer (kind=c_int) function omp_target_associate_ptr(host_ptr, &
device_ptr, size, device_offset, device_num) bind(c)
use, intrinsic :: iso_c_binding, only : c_int, c_ptr, &
c_size_t
type (c_ptr), value, intent(in) :: host_ptr, device_ptr
integer (kind=c_size_t), value :: size, device_offset
integer (kind=c_int), value :: device_num
                                                        Fortran
Effect
The omp_target_associate_ptr routine associates a device pointer in the device data
environment of device device_num with a host pointer such that when the host device pointer
appears in a subsequent map clause, the associated device pointer is used as the target for data
motion associated with that host pointer. Thus, the omp_target_associate_ptr routine
maps a device pointer, which may be returned from omp_target_alloc or implementation
defined routine, to a host pointer. The device_offset argument specifies the offset into device_ptr
that is used as the base address for the device side of the mapping. The reference count of the
resulting mapping will be infinite. The association between the host pointer and the device pointer
can be removed by using the omp_target_disassociate_ptr routine. The routine returns
zero if successful. Otherwise it returns a non-zero value.
Only one device buffer can be associated with a given host pointer value and device number pair.
Attempting to associate a second buffer will return non-zero. Associating the same pair of pointers
on the same device with the same offset has no effect and returns zero. Associating pointers that
share underlying storage will result in unspecified behavior. The omp_target_is_present
routine can be used to test whether a given host pointer has a corresponding list item in the device
data environment.

Execution Model Events
The target-data-associate event occurs before a thread initiates a device pointer association on a
target device.

Tool Callbacks
A thread dispatches a registered target_data_op_emi callback with
ompt_scope_beginend as its endpoint argument for each occurrence of a
target-data-associate event in that thread.

Cross References
• omp_target_alloc Routine, see Section 25.3
• omp_target_disassociate_ptr Routine, see Section 25.6
• omp_target_is_present Routine, see Section 25.2.1

• OMPT scope_endpoint Type, see Section 33.27
• target_data_op_emi Callback, see Section 35.7
