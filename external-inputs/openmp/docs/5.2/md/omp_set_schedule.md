<!-- source: OpenMP API Specification, section 18.2.11 (omp_set_schedule) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.11 omp_set_schedule

Summary
The omp_set_schedule routine affects the schedule that is applied when runtime is used as
schedule kind, by setting the value of the run-sched-var ICV.

Format
                                                C / C++
void omp_set_schedule(omp_sched_t kind, int chunk_size);
                                                C / C++
                                                Fortran
subroutine omp_set_schedule(kind, chunk_size)
integer (kind=omp_sched_kind) kind
integer chunk_size
                                                 Fortran
Constraints on Arguments
The first argument passed to this routine can be one of the valid OpenMP schedule kinds (except for
runtime) or any implementation-specific schedule. The C/C++ header file (omp.h) and the
Fortran include file (omp_lib.h) and/or Fortran module file (omp_lib) define the valid
constants. The valid constants must include the following, which can be extended with
implementation-specific values:
                                                C / C++
typedef enum omp_sched_t {
// schedule kinds
omp_sched_static = 0x1,
omp_sched_dynamic = 0x2,
omp_sched_guided = 0x3,
omp_sched_auto = 0x4,
22
// schedule modifier
omp_sched_monotonic = 0x80000000u
} omp_sched_t;
                                                C / C++
                                                Fortran
! schedule kinds
integer(kind=omp_sched_kind), &
parameter :: omp_sched_static = &
int(Z’1’, kind=omp_sched_kind)
integer(kind=omp_sched_kind), &
parameter :: omp_sched_dynamic = &
int(Z’2’, kind=omp_sched_kind)

integer(kind=omp_sched_kind), &
parameter :: omp_sched_guided = &
int(Z’3’, kind=omp_sched_kind)
integer(kind=omp_sched_kind), &
parameter :: omp_sched_auto = &
int(Z’4’, kind=omp_sched_kind)
 7
! schedule modifier
integer(kind=omp_sched_kind), &
parameter :: omp_sched_monotonic = &
int(Z’80000000’, kind=omp_sched_kind)
                                                        Fortran
Binding
The binding task set for an omp_set_schedule region is the generating task.

Effect
The effect of this routine is to set the value of the run-sched-var ICV of the current task to the
values specified in the two arguments. The schedule is set to the schedule kind that is specified by
the first argument kind. It can be any of the standard schedule kinds or any other
implementation-specific one. For the schedule kinds static, dynamic, and guided, the
chunk_size is set to the value of the second argument, or to the default chunk_size if the value of the
second argument is less than 1; for the schedule kind auto, the second argument has no meaning;
for implementation-specific schedule kinds, the values and associated meanings of the second
argument are implementation defined.
Each of the schedule kinds can be combined with the omp_sched_monotonic modifier by
using the + or | operators in C/C++ or the + operator in Fortran. If the schedule kind is combined
with the omp_sched_monotonic modifier, the schedule is modified as if the monotonic
schedule modifier was specified. Otherwise, the schedule modifier is nonmonotonic.

Cross References
• run-sched-var ICV, see Table 2.1
