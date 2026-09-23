<!-- source: OpenMP API Specification, section 18.2.12 (omp_get_schedule) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.12 omp_get_schedule

Summary
The omp_get_schedule routine returns the schedule that is applied when the runtime schedule
is used.

Format
                                                        C / C++
void omp_get_schedule(omp_sched_t *kind, int *chunk_size);
                                                        C / C++

                                                 Fortran
subroutine omp_get_schedule(kind, chunk_size)
integer (kind=omp_sched_kind) kind
integer chunk_size
                                                 Fortran
Binding
The binding task set for an omp_get_schedule region is the generating task.

Effect
This routine returns the run-sched-var ICV in the task to which the routine binds. The first
argument kind returns the schedule to be used. It can be any of the standard schedule kinds as
defined in Section 18.2.11, or any implementation-specific schedule kind. If the returned schedule
kind is static, dynamic, or guided, the second argument chunk_size returns the chunk size to
be used, or a value less than 1 if the default chunk size is to be used. The value returned by the
second argument is implementation defined for any other schedule kinds.

Cross References
• run-sched-var ICV, see Table 2.1
