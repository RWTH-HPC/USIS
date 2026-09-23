<!-- source: OpenMP API Specification, section 23.2.1 (omp_fulfill_event Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.2.1 omp_fulfill_event Routine

Name: omp_fulfill_event                                     Properties: default
24
      Category: subroutine

Arguments
            Name                                          Type                          Properties
2
            event                                         event_handle                  default

Prototypes
                                                         C / C++
void omp_fulfill_event(omp_event_handle_t event);
                                                         C / C++
                                                         Fortran
subroutine omp_fulfill_event(event)
integer (kind=omp_event_handle_kind) event
                                                          Fortran
Effect
The effect of this routine is to fulfill the event associated with the event argument. The effect of
fulfilling the event will depend on how the event object was created. The event object is destroyed
and cannot be accessed after calling this routine, and the event handle becomes unassociated with
any event object. This routine has no effect if the event argument corresponds to a completed task.

Execution Model Events
The task-fulfill event occurs in a thread that executes an omp_fulfill_event region before the
event is fulfilled if the OpenMP event object was created by a detach clause on a task.

Tool Callbacks
A thread dispatches a registered task_schedule callback with NULL as its next_task_data
argument while the argument prior_task_data binds to the detachable task for each occurrence of a
task-fulfill event. If the task-fulfill event occurs before the detachable task finished execution of the
associated structured block, the callback has ompt_task_early_fulfill as its
prior_task_status argument; otherwise the callback has ompt_task_late_fulfill as its
prior_task_status argument.

Restrictions
Restrictions to the omp_fulfill_event routine are as follows:
• The event that corresponds to the event argument must not have already been fulfilled.
• The event handle that the event argument identifies must have been created by the effect of a
detach clause.
• The event handle passed to the routine must refer to an event object that was created by a
thread in the same device as the thread that invoked the routine.
• An event handle must be fulfilled before execution continues beyond the next barrier of the
current team after a detach clause creates the event that the event argument represents.

Cross References
• detach Clause, see Section 14.11
• OpenMP event_handle Type, see Section 20.6.1
• task_schedule Callback, see Section 34.5.2
• OMPT task_status Type, see Section 33.38
