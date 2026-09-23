<!-- source: OpenMP API Specification, section 23.1.3 (omp_in_final Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 23 Tasking Support Routines -->

# 23.1.3 omp_in_final Routine

Name: omp_in_final                                   Properties: ICV-retrieving
15
      Category: function

Return Type
      Name                                       Type                   Properties
17
      <return type>                              logical                default

Prototypes
                                                 C / C++
int omp_in_final(void);
                                                 C / C++
                                                 Fortran
logical function omp_in_final()
                                                 Fortran

Effect
The omp_in_final routine returns the value of the final-task-var ICV, which indicates whether
the encountering task is a final task region.

Cross References
• final Clause, see Section 14.7
• final-task-var ICV, see Table 3.1
• task Construct, see Section 14.1
