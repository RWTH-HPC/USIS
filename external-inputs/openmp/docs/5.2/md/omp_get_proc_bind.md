<!-- source: OpenMP API Specification, section 18.3.1 (omp_get_proc_bind) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.1 omp_get_proc_bind

Summary
The omp_get_proc_bind routine returns the thread affinity policy to be used for the
subsequent nested parallel regions that do not specify a proc_bind clause.

Format
                                                   C / C++
omp_proc_bind_t omp_get_proc_bind(void);
                                                   C / C++
                                                   Fortran
integer (kind=omp_proc_bind_kind) function omp_get_proc_bind()
                                                    Fortran
Constraints on Arguments
The value returned by this routine must be one of the valid affinity policy kinds. The C/C++ header
file (omp.h) and the Fortran include file (omp_lib.h) and/or Fortran module file (omp_lib)
define the valid constants. The valid constants must include the following:
                                                   C / C++
typedef enum omp_proc_bind_t {
omp_proc_bind_false = 0,
omp_proc_bind_true = 1,
omp_proc_bind_primary = 2,
omp_proc_bind_master = omp_proc_bind_primary, // (deprecated)
omp_proc_bind_close = 3,
omp_proc_bind_spread = 4
} omp_proc_bind_t;
                                                   C / C++
                                                   Fortran
integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_false = 0
integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_true = 1
integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_primary = 2

integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_master = &
omp_proc_bind_primary         ! (deprecated)
integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_close = 3
integer (kind=omp_proc_bind_kind), &
parameter :: omp_proc_bind_spread = 4
                                                         Fortran
Binding
The binding task set for an omp_get_proc_bind region is the generating task.

Effect
The effect of this routine is to return the value of the first element of the bind-var ICV of the current
task. See Section 10.1.3 for the rules that govern the thread affinity policy.

Cross References
• Controlling OpenMP Thread Affinity, see Section 10.1.3
• bind-var ICV, see Table 2.1
• parallel directive, see Section 10.1
