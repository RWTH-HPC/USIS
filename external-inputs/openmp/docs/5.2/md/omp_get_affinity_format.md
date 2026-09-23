<!-- source: OpenMP API Specification, section 18.3.9 (omp_get_affinity_format) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.9 omp_get_affinity_format

Summary
The omp_get_affinity_format routine returns the value of the affinity-format-var ICV on
the device.

Format
                                                C / C++
size_t omp_get_affinity_format(char *buffer, size_t size);
                                                C / C++
                                                Fortran
integer function omp_get_affinity_format(buffer)
character(len=*),intent(out) :: buffer
                                                Fortran
Binding
When called from a sequential part of the program, the binding thread set for an
omp_get_affinity_format region is the encountering thread. When called from within any
parallel or teams region, the binding thread set (and binding region, if required) for the
omp_get_affinity_format region is implementation defined.

Effect
                                                          C / C++
The omp_get_affinity_format routine returns the number of characters in the
affinity-format-var ICV on the current device, excluding the terminating null byte (’\0’) and if
size is non-zero, writes the value of the affinity-format-var ICV on the current device to buffer
followed by a null byte. If the return value is larger or equal to size, the affinity format specification
is truncated, with the terminating null byte stored to buffer[size-1]. If size is zero, nothing is
stored and buffer may be NULL.
                                                          C / C++
                                                          Fortran
The omp_get_affinity_format routine returns the number of characters that are required to
hold the affinity-format-var ICV on the current device and writes the value of the
affinity-format-var ICV on the current device to buffer. If the return value is larger than
len(buffer), the affinity format specification is truncated.
                                                          Fortran
If the buffer argument does not conform to the specified format then the result is implementation
defined.

Cross References
• affinity-format-var ICV, see Table 2.1
• parallel directive, see Section 10.1
• teams directive, see Section 10.2
