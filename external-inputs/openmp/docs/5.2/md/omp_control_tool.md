<!-- source: OpenMP API Specification, section 18.14 (Tool Control Routine) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.14 Tool Control Routine

Summary
The omp_control_tool routine enables a program to pass commands to an active tool.

Format
                                               C / C++
int omp_control_tool(int command, int modifier, void *arg);
                                               C / C++
                                               Fortran
integer function omp_control_tool(command, modifier)
integer (kind=omp_control_tool_kind) command
integer modifier
                                               Fortran
Constraints on Arguments
The following enumeration type defines four standard commands. Table 18.3 describes the actions
that these commands request from a tool.

                                                       C / C++
typedef enum omp_control_tool_t {
omp_control_tool_start = 1,
omp_control_tool_pause = 2,
omp_control_tool_flush = 3,
omp_control_tool_end = 4
} omp_control_tool_t;
                                                       C / C++
                                                       Fortran
integer (kind=omp_control_tool_kind), &
parameter :: omp_control_tool_start                         = 1
integer (kind=omp_control_tool_kind), &
parameter :: omp_control_tool_pause                         = 2
integer (kind=omp_control_tool_kind), &
parameter :: omp_control_tool_flush                         = 3
integer (kind=omp_control_tool_kind), &
parameter :: omp_control_tool_end =                         4
                                                       Fortran
Tool-specific values for command must be greater or equal to 64. Tools must ignore command
values that they are not explicitly designed to handle. Other values accepted by a tool for command,
and any values for modifier and arg are tool-defined.

           TABLE 18.3: Standard Tool Control Commands
            Command                                Action

            omp_control_tool_start                 Start or restart monitoring if it is off. If monitoring
                                                   is already on, this command is idempotent. If moni-
                                                   toring has already been turned off permanently, this
                                                   command will have no effect.
            omp_control_tool_pause                 Temporarily turn monitoring off. If monitoring is
                                                   already off, it is idempotent.
            omp_control_tool_flush                 Flush any data buffered by a tool. This command may
                                                   be applied whether monitoring is on or off.
            omp_control_tool_end                   Turn monitoring off permanently; the tool finalizes
                                                   itself and flushes all output.

Binding
The binding task set for an omp_control_tool region is the generating task.

Effect
An OpenMP program may use omp_control_tool to pass commands to a tool. An application
can use omp_control_tool to request that a tool starts or restarts data collection when a code
region of interest is encountered, that a tool pauses data collection when leaving the region of
interest, that a tool flushes any data that it has collected so far, or that a tool ends data collection.
Additionally, omp_control_tool can be used to pass tool-specific commands to a particular
tool. The following types correspond to return values from omp_control_tool:
                                                   C / C++
typedef enum omp_control_tool_result_t {
omp_control_tool_notool = -2,
omp_control_tool_nocallback = -1,
omp_control_tool_success = 0,
omp_control_tool_ignored = 1
} omp_control_tool_result_t;
                                                   C / C++
                                                   Fortran
integer (kind=omp_control_tool_result_kind), &
parameter :: omp_control_tool_notool = -2
integer (kind=omp_control_tool_result_kind), &
parameter :: omp_control_tool_nocallback = -1
integer (kind=omp_control_tool_result_kind), &
parameter :: omp_control_tool_success = 0
integer (kind=omp_control_tool_result_kind), &
parameter :: omp_control_tool_ignored = 1
                                                   Fortran
If the OMPT interface state is inactive, the OpenMP implementation returns
omp_control_tool_notool. If the OMPT interface state is active, but no callback is
registered for the tool-control event, the OpenMP implementation returns
omp_control_tool_nocallback. An OpenMP implementation may return other
implementation-defined negative values strictly smaller than -64; an application may assume that
any negative return value indicates that a tool has not received the command. A return value of
omp_control_tool_success indicates that the tool has performed the specified command. A
return value of omp_control_tool_ignored indicates that the tool has ignored the specified
command. A tool may return other positive values strictly greater than 64 that are tool-defined.

Execution Model Events
The tool-control event occurs in the thread that encounters a call to omp_control_tool at a
point inside its corresponding OpenMP region.

Tool Callbacks
A thread dispatches a registered ompt_callback_control_tool callback for each
occurrence of a tool-control event. The callback executes in the context of the call that occurs in the
user program and has type signature ompt_callback_control_tool_t. The callback may
return any non-negative value, which will be returned to the application by the OpenMP
implementation as the return value of the omp_control_tool call that triggered the callback.
Arguments passed to the callback are those passed by the user to omp_control_tool. If the
call is made in Fortran, the tool will be passed NULL as the third argument to the callback. If any of
the four standard commands is presented to a tool, the tool will ignore the modifier and arg
argument values.

Restrictions
Restrictions on access to the state of an OpenMP first-party tool are as follows:
• An application may access the tool state modified by an OMPT callback only by using
omp_control_tool.

Cross References
• OMPT Interface, see Chapter 19
• ompt_callback_control_tool_t, see Section 19.5.2.29
