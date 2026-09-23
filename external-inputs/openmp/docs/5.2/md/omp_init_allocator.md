<!-- source: OpenMP API Specification, section 18.13.2 (omp_init_allocator) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.13.2 omp_init_allocator

Summary
The omp_init_allocator routine initializes an allocator and associates it with a memory
space.
Format
                                                   C / C++
omp_allocator_handle_t omp_init_allocator (
omp_memspace_handle_t memspace,
int ntraits,
const omp_alloctrait_t traits[]
);
                                                   C / C++
                                                   Fortran
integer(kind=omp_allocator_handle_kind) &
function omp_init_allocator ( memspace, ntraits, traits )
integer(kind=omp_memspace_handle_kind),intent(in) :: memspace
integer,intent(in) :: ntraits
type(omp_alloctrait),intent(in) :: traits(*)
                                                   Fortran
Constraints on Arguments
The memspace argument must be one of the predefined memory spaces defined in Table 6.1. If the
ntraits argument is greater than zero then the traits argument must specify at least that many traits.
If it specifies fewer than ntraits traits the behavior is unspecified.
Binding
The binding thread set for an omp_init_allocator region is all threads on a device. The
effect of executing this routine is not related to any specific region that corresponds to any construct
or API routine.
Effect
The omp_init_allocator routine creates a new allocator that is associated with the
memspace memory space and returns a handle to it. All allocations through the created allocator
will behave according to the allocator traits specified in the traits argument. The number of traits in
the traits argument is specified by the ntraits argument. Specifying the same allocator trait more
than once results in unspecified behavior. The routine returns a handle for the created allocator. If
the special omp_atv_default value is used for a given trait, then its value will be the default
value specified in Table 6.2 for that given trait.
If memspace is omp_default_mem_space and the traits argument is an empty set this routine
will always return a handle to an allocator. Otherwise if an allocator based on the requirements
cannot be created then the special omp_null_allocator handle is returned.

Restrictions
The restrictions to the omp_init_allocator routine are as follows:
• The use of an allocator returned by this routine on a device other than the one on which it was
created results in unspecified behavior.
• Unless a requires directive with the dynamic_allocators clause is present in the same
compilation unit, using this routine in a target region results in unspecified behavior.

Cross References
• Memory Allocators, see Section 6.2
• Memory Spaces, see Section 6.1
• requires directive, see Section 8.2
• target directive, see Section 13.8
