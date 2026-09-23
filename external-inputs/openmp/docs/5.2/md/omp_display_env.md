<!-- source: OpenMP API Specification, section 18.15 (Environment Display Routine) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.15 Environment Display Routine

Summary
The omp_display_env routine displays the OpenMP version number and the initial values of
ICVs associated with the environment variables described in Chapter 21.

Format
                                                        C / C++
void omp_display_env(int verbose);
                                                        C / C++
                                                        Fortran
subroutine omp_display_env(verbose)
logical,intent(in) :: verbose
                                                        Fortran
Binding
The binding thread set for an omp_display_env region is the encountering thread.

Effect
Each time the omp_display_env routine is invoked, the runtime system prints the OpenMP
version number and the initial values of the ICVs associated with the environment variables
described in Chapter 21. The displayed values are the values of the ICVs after they have been
modified according to the environment variable settings and before the execution of any OpenMP
construct or API routine.
The display begins with "OPENMP DISPLAY ENVIRONMENT BEGIN", followed by the
_OPENMP version macro (or the openmp_version named constant for Fortran) and ICV values,
in the format NAME ’=’ VALUE. NAME corresponds to the macro or environment variable name,
optionally prepended with a bracketed DEVICE. VALUE corresponds to the value of the macro or
ICV associated with this environment variable. Values are enclosed in single quotes. DEVICE
corresponds to the device on which the value of the ICV is applied. The display is terminated with
"OPENMP DISPLAY ENVIRONMENT END".
For the OMP_NESTED environment variable, the printed value is true if the max-active-levels-var
ICV is initialized to a value greater than 1; otherwise the printed value is false. The OMP_NESTED
environment variable has been deprecated.
If the verbose argument evaluates to false, the runtime displays the OpenMP version number
defined by the _OPENMP version macro (or the openmp_version named constant for Fortran)
value and the initial ICV values for the environment variables listed in Chapter 21. If the verbose
argument evaluates to true, the runtime may also display the values of vendor-specific ICVs that
may be modified by vendor-specific environment variables.
Example output:
OPENMP DISPLAY ENVIRONMENT BEGIN
_OPENMP=’202111’
[host] OMP_SCHEDULE=’GUIDED,4’
[host] OMP_NUM_THREADS=’4,3,2’
[device] OMP_NUM_THREADS=’2’
[host,device] OMP_DYNAMIC=’TRUE’
[host] OMP_PLACES=’{0:4},{4:4},{8:4},{12:4}’
...
OPENMP DISPLAY ENVIRONMENT END

Restrictions
Restrictions to the omp_display_env routine are as follows.
• When called from within a target region the effect is unspecified.

Cross References
• OMP_DISPLAY_ENV, see Section 21.7
