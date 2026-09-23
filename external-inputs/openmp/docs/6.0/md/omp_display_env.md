<!-- source: OpenMP API Specification, section 30.4 (omp_display_env Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.4 omp_display_env Routine

Name: omp_display_env                                     Properties: default
 8
            Category: subroutine

Arguments
            Name                                        Type                        Properties
10
            verbose                                     logical                     intent(in)

Prototypes
                                                       C / C++
void omp_display_env(int verbose);
                                                       C / C++
                                                       Fortran
subroutine omp_display_env(verbose)
logical, intent(in) :: verbose
                                                        Fortran
Effect
Each time that the omp_display_env routine is invoked, the runtime system prints the OpenMP
version number and the initial values of the ICVs associated with the environment variables
described in Chapter 4. The displayed values are the values of the ICVs after they have been
modified according to the environment variable settings and before the execution of any construct
or routine.
The display begins with "OPENMP DISPLAY ENVIRONMENT BEGIN", followed by the
_OPENMP version macro (or the openmp_version predefined identifier for Fortran) and ICV
values, in the format NAME ’=’ VALUE. NAME corresponds to the macro or environment variable
name, prepended with a bracketed DEVICE. VALUE corresponds to the value of the macro or ICV
associated with this environment variable. Values are enclosed in single quotes. DEVICE
corresponds to a comma-separated list of the devices on which the value of the ICV is applied. It is
host if the device is the host device; device if the ICV applies to all non-host devices; all if
the ICV has global scope or the value applies to the host device and all non-host devices; dev, a
space, and the device number if it applies to a specific non-host devices. Instead of a single number
a range can also be specified using the first and last device number separated by a hyphen. Whether

ICVs with the same value are combined or displayed in multiple lines is implementation defined.
The display is terminated with "OPENMP DISPLAY ENVIRONMENT END".
If the verbose argument evaluates to false, the runtime displays the OpenMP version number
defined by the _OPENMP version macro (or the openmp_version predefined identifier for
Fortran) value and the initial ICV values for the environment variables listed in Chapter 4. If the
verbose argument evaluates to true, the runtime may also display the values of vendor-specific
ICVs that may be modified by vendor-specific environment variables.
Example output:
OPENMP DISPLAY ENVIRONMENT BEGIN
_OPENMP='202411'
[dev 1] OMP_SCHEDULE='GUIDED,4'
[host] OMP_NUM_THREADS='4,3,2'
[device] OMP_NUM_THREADS='2'
[host, dev 2] OMP_DYNAMIC='TRUE'
[dev 2-3, dev 5] OMP_DYNAMIC='FALSE'
[all] OMP_WAIT_POLICY='ACTIVE'
[host] OMP_PLACES='{0:4},{4:4},{8:4},{12:4}'
...
OPENMP DISPLAY ENVIRONMENT END
Restrictions
Restrictions to the omp_display_env routine are as follows:
• When called from within a target region the effect is unspecified.
Cross References
• Predefined Identifiers, see Section 20.1
