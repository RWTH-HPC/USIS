<!-- source: OpenMP API Specification, section 31.1 (omp_control_tool Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 31 Tool Support Routines -->

# 31.1 omp_control_tool Routine

Name: omp_control_tool                                      Properties: default
 4
            Category: function
Return Type and Arguments
            Name                                          Type                          Properties
            <return type>                                 control_tool_result           default
command                                       control_tool                  omp
            modifier                                      integer                       default
            arg                                           void                          C/C++ pointer

Prototypes
                                                         C / C++
omp_control_tool_result_t omp_control_tool(
omp_control_tool_t command, int modifier, void *arg);
                                                         C / C++
                                                         Fortran
integer (kind=omp_control_tool_result_kind) function &
omp_control_tool(command, modifier)
integer (kind=omp_control_tool_kind) command
integer modifier
                                                          Fortran
Effect
An OpenMP program may use the omp_control_tool routine to pass commands to a tool. An
OpenMP program can use the routine to request: that a tool starts or restarts data collection when a
code region of interest is encountered; that a tool pauses data collection when leaving the region of
interest; that a tool flushes any data that it has collected so far; or that a tool ends data collection.
Additionally, the omp_control_tool routine can be used to pass tool-specific commands to a
particular tool.

Any values for modifier and arg are tool defined.
If the OMPT interface state is OMPT inactive, the OpenMP implementation returns
omp_control_tool_notool. If the OMPT interface state is OMPT active, but no callback is
registered for the tool-control event, the OpenMP implementation returns
omp_control_tool_nocallback. An OpenMP implementation may return other
implementation defined negative values strictly smaller than -64; an OpenMP program may assume
that any negative return value indicates that a tool has not received the command. A return value of
omp_control_tool_success indicates that the tool has performed the specified command. A
return value of omp_control_tool_ignored indicates that the tool has ignored the specified
command. A tool may return other positive values strictly greater than 64 that are tool defined.

Execution Model Events
The tool-control event occurs in the encountering thread inside the corresponding region.

Tool Callbacks
A thread dispatches a registered control_tool callback for each occurrence of a tool-control
event. The callback executes in the context of the call that occurs in the user program. The callback
may return any non-negative value, which will be returned to the OpenMP program by the OpenMP
implementation as the return value of the omp_control_tool call that triggered the callback.
Arguments passed to the callback are those passed by the user to omp_control_tool. If the call
is made in Fortran, the tool will be passed NULL as the third argument to the callback. If any of the
standard commands is presented to a tool, the tool will ignore the modifier and arg argument values.

Restrictions
Restrictions on access to the state of an OpenMP first-party tool are as follows:
• An OpenMP program may access the tool state modified by an OMPT callback only by using
omp_control_tool.

Cross References
• control_tool Callback, see Section 34.8
• OpenMP control_tool Type, see Section 20.12.1
• OpenMP control_tool_result Type, see Section 20.12.2
• OMPT Overview, see Chapter 32

Part IV

OMPT
