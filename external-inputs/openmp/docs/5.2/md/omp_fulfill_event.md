<!-- source: OpenMP API Specification, section 18.11.1 (omp_fulfill_event) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.11.1 omp_fulfill_event

Summary
This routine fulfills and destroys an OpenMP event.

Format
                                                   C / C++
void omp_fulfill_event(omp_event_handle_t event);
                                                   C / C++
                                                   Fortran
subroutine omp_fulfill_event(event)
integer (kind=omp_event_handle_kind) event
                                                   Fortran
Constraints on Arguments
A program that calls this routine on an event that was already fulfilled is non-conforming. A
program that calls this routine with an event handle that was not created by the detach clause is
non-conforming.

Effect
The effect of this routine is to fulfill the event associated with the event handle argument. The effect
of fulfilling the event will depend on how the event was created. The event is destroyed and cannot
be accessed after calling this routine, and the event handle becomes unassociated with any event.

Execution Model Events
The task-fulfill event occurs in a thread that executes an omp_fulfill_event region before the
event is fulfilled if the OpenMP event object was created by a detach clause on a task.

Tool Callbacks
A thread dispatches a registered ompt_callback_task_schedule callback with NULL as its
next_task_data argument while the argument prior_task_data binds to the detachable task for each
occurrence of a task-fulfill event. If the task-fulfill event occurs before the detachable task finished
the execution of the associated structured-block, the callback has
ompt_task_early_fulfill as its prior_task_status argument; otherwise the callback has
ompt_task_late_fulfill as its prior_task_status argument. This callback has type
signature ompt_callback_task_schedule_t.

Restrictions
Restrictions to the omp_fulfill_event routine are as follows:
• The event handler passed to the routine must have been created by a thread in the same device as
the thread that invoked the routine.

Cross References
• ompt_callback_task_schedule_t, see Section 19.5.2.10
• detach clause, see Section 12.5.2

           TABLE 18.1: Required Values of the omp_interop_property_t enum Type

            Enum Name                          Contexts     Name           Property
            omp_ipr_fr_id = -1                 all          fr_id          An intptr_t value that rep-
                                                                           resents the foreign runtime id of
                                                                           context
            omp_ipr_fr_name = -2               all          fr_name        C string value that represents the
                                                                           foreign runtime name of context
            omp_ipr_vendor = -3                all          vendor         An intptr_t that represents
                                                                           the vendor of context
            omp_ipr_vendor_name =              all          vendor_name    C string value that represents the
            -4                                                             vendor of context
            omp_ipr_device_num = -5            all          device_num     The OpenMP device ID for
                                                                           the device in the range 0 to
                                                                           omp_get_num_devices()
                                                                           inclusive
            omp_ipr_platform = -6              target       platform       A foreign platform handle usu-
                                                                           ally spanning multiple devices
            omp_ipr_device = -7                target       device         A foreign device handle
            omp_ipr_device_context             target       device_context A handle to an instance of a
            = -8                                                           foreign device context
            omp_ipr_targetsync = -9            targetsync   targetsync     A handle to a synchronization
                                                                           object of a foreign execution
                                                                           context
            omp_ipr_first = -9

                                                        C / C++
