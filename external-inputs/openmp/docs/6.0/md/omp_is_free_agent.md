<!-- source: OpenMP API Specification, section 23.1.4 (omp_is_free_agent Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.1.4 omp_is_free_agent Routine

Name: omp_is_free_agent                                   Properties: ICV-retrieving
 9
            Category: function

Return Type
            Name                                        Type                         Properties
11
            <return type>                               logical                      default

Prototypes
                                                        C / C++
int omp_is_free_agent(void);
                                                        C / C++
                                                        Fortran
logical function omp_is_free_agent()
                                                        Fortran
Effect
The omp_is_free_agent routine returns the value of the free-agent-var ICV, which indicates
whether a free-agent thread is executing the enclosing task region at the time the routine is called.

Cross References
• free-agent-var ICV, see Table 3.1
• task Construct, see Section 14.1
• threadset Clause, see Section 14.8
