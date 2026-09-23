<!-- source: OpenMP API Specification, section 27.6 (omp_init_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.6 omp_init_allocator Routine

Name: omp_init_allocator                                  Properties: all-device-threads-binding,
23
            Category: function                                        memory-management-routine
Return Type and Arguments
            Name                                       Type                         Properties
            <return type>                              allocator_handle             default
memspace                                   memspace_handle              intent(in), omp
            ntraits                                    integer                      intent(in)
            traits                                     alloctrait                   intent(in), pointer, omp

Prototypes
                                                   C / C++
omp_allocator_handle_t omp_init_allocator(
omp_memspace_handle_t memspace, int ntraits,
const omp_alloctrait_t *traits);
                                                   C / C++
                                                   Fortran
integer (kind=omp_allocator_handle_kind) function &
omp_init_allocator(memspace, ntraits, traits)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
integer, intent(in) :: ntraits
integer (kind=omp_alloctrait_kind), intent(in) :: traits(*)
                                                    Fortran
Effect
The omp_init_allocator routine creates a new allocator that is associated with the
memspace memory space and returns a handle to it. All allocations through the created allocator
will behave according to the allocator traits specified in the traits argument. The number of traits in
the traits argument is specified by the ntraits argument. If the special omp_atv_default value
is used for a given trait, then its value will be the default value specified in Table 8.2 for that trait.
If memspace has the value omp_null_mem_space, the effect of this routine will be as if the
value of memspace was omp_default_mem_space. If memspace is
omp_default_mem_space and the traits argument is an empty set, this routine will always
return a handle to an allocator. Otherwise, if an allocator based on the requirements cannot be
created then the special omp_null_allocator handle is returned.

Restrictions
The restrictions to the omp_init_allocator routine are as follows:
• Each allocator trait must be specified at most once.
• The memspace argument must be a valid memory space handle or the value
omp_null_mem_space.
• If the ntraits argument is positive then the traits argument must specify at least ntraits traits.
• The use of an allocator returned by this routine on devices other than the one on which it was
created results in unspecified behavior.
• Unless a requires directive with the dynamic_allocators clause is present in the
same compilation unit, using this routine in a target region results in unspecified behavior.
• If the memspace handle represents a target memory space, the values omp_atv_device,
omp_atv_cgroup, omp_atv_pteam or omp_atv_thread must not be specified for
the omp_atk_access allocator trait.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocators, see Section 8.2
• Memory Spaces, see Section 8.1
• OpenMP memspace_handle Type, see Section 20.8.11
• requires Directive, see Section 10.5
• target Construct, see Section 15.8
