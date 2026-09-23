<!-- source: OpenMP API Specification, section 29.1 (omp_get_proc_bind Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.1 omp_get_proc_bind Routine

Name: omp_get_proc_bind                                     Properties: ICV-retrieving
 5
            Category: function

Return Type
            Name                                         Type                          Properties
 7
            <return type>                                proc_bind                     default

Prototypes
                                                         C / C++
omp_proc_bind_t omp_get_proc_bind(void);
                                                         C / C++
                                                         Fortran
integer (kind=omp_proc_bind_kind) function omp_get_proc_bind()
                                                         Fortran
Effect
The effect of this routine is to return the value of the first element of the bind-var ICV of the current
task, which will be used for the subsequent nested parallel regions that do not specify a
proc_bind clause. See Section 12.1.3 for the rules that govern the thread affinity policy.

Cross References
• Controlling OpenMP Thread Affinity, see Section 12.1.3
• bind-var ICV, see Table 3.1
• parallel Construct, see Section 12.1
• OpenMP proc_bind Type, see Section 20.10.1
