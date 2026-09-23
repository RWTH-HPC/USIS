<!-- source: OpenMP API Specification, section 27.5.5 (omp_mempartition_set_part Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.5.5 omp_mempartition_set_part Routine

Name: omp_mempartition_set_part                           Properties: all-device-threads-binding,
Category: function                                        iso_c_binding, memory-management-
                                                                      routine, memory-partitioning
Return Type and Arguments
            Name                                       Type                         Properties
            <return type>                              integer                      default
            partition                                  mempartition                 C/C++ pointer, omp,
intent(out)
            part                                       c_size_t                     intent(in), iso_c
            resource                                   integer                      intent(in), iso_c
            size                                       c_size_t                     intent(in), iso_c

Prototypes
                                                   C / C++
int omp_mempartition_set_part(omp_mempartition_t *partition,
size_t part, int resource, size_t size);
                                                   C / C++
                                                   Fortran
integer function omp_mempartition_set_part(partition, part, &
resource, size) bind(c)
use, intrinsic :: iso_c_binding, only : c_size_t
integer (kind=omp_mempartition_kind), intent(out) :: partition
integer (kind=c_size_t), intent(in) :: part, size
integer, intent(in) :: resource
                                                   Fortran
Effect
The effect of the omp_mempartition_set_part routine is to define the size and resource of a
given part of a memory partition. Thus the routine defines the part number indicated by the part
argument of the memory partition object indicated by the partition argument to be associated to the
resource indicated by the resource argument and to be of size indicated by the size argument.
The size of all parts of a memory partition, except the last one, need to be a multiple of the page size
that the memory space where the memory is being allocated supports. If the specified size cannot
be supported by the specified resource, this routine returns negative one. Otherwise, it returns zero.

Restrictions
The restrictions to the omp_mempartition_set_part routine are as follows:
• The memory partition represented by the partition argument must be in the initialized state.
• This routine must only be called by a procedure that is associated with the memory
partitioner object that allocated the memory partition indicated by the partition argument.
Cross References
• Memory Spaces, see Section 8.1
• OpenMP Memory Management Types, see Section 20.8
• OpenMP mempartitioner Type, see Section 20.8.7
