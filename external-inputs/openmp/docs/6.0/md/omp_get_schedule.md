<!-- source: OpenMP API Specification, section 21.10 (omp_get_schedule Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.10 omp_get_schedule Routine

Name: omp_get_schedule                                     Properties: ICV-retrieving
11
            Category: subroutine

Arguments
            Name                                         Type                         Properties
kind                                         sched                        C/C++ pointer, omp
            chunk_size                                   integer                      C/C++ pointer

Prototypes
                                                        C / C++
void omp_get_schedule(omp_sched_t *kind, int *chunk_size);
                                                        C / C++
                                                        Fortran
subroutine omp_get_schedule(kind, chunk_size)
integer (kind=omp_sched_kind) kind
integer chunk_size
                                                        Fortran
Effect
The omp_get_schedule routine returns the run-sched-var ICV in the task to which the routine
binds. Thus, the routine returns the schedule that is applied when the runtime schedule type is
used. The first argument kind returns the schedule type to be used. If the returned schedule type is
omp_sched_static, omp_sched_dynamic, or omp_sched_guided, the second
argument, chunk_size, returns the chunk size to be used, or a value less than 1 if the default chunk
size is to be used. The value returned by the second argument is implementation defined for any
other schedule types.

Cross References
• run-sched-var ICV, see Table 3.1
• OpenMP sched Type, see Section 20.5.1
