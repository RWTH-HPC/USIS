<!-- source: OpenMP API Specification, section 21.9 (omp_set_schedule Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.9 omp_set_schedule Routine

Name: omp_set_schedule                                   Properties: ICV-modifying
12
      Category: subroutine

Arguments
      Name                                        Type                        Properties
kind                                        sched                       omp
      chunk_size                                  integer                     default

Prototypes
                                                 C / C++
void omp_set_schedule(omp_sched_t kind, int chunk_size);
                                                 C / C++
                                                 Fortran
subroutine omp_set_schedule(kind, chunk_size)
integer (kind=omp_sched_kind) kind
integer chunk_size
                                                 Fortran
Effect
The effect of this routine is to set the value of the run-sched-var ICV of the current task to the
values specified in the two arguments. Thus, the routine affects the schedule that is applied when
runtime is used as the schedule type.

The schedule is set to the schedule type that is specified by the first argument kind. For the schedule
types omp_sched_static, omp_sched_dynamic, and omp_sched_guided, the
chunk_size is set to the value of the second argument, or to the default chunk_size if the value of the
second argument is less than 1; for the schedule type omp_sched_auto, the second argument is
ignored; for implementation defined schedule types, the values and associated meanings of the
second argument are implementation defined.

Cross References
• run-sched-var ICV, see Table 3.1
• OpenMP sched Type, see Section 20.5.1
