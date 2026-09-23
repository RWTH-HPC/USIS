<!-- source: OpenMP API Specification, section 18.3.11 (omp_capture_affinity) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.11 omp_capture_affinity

Summary
The omp_capture_affinity routine prints the OpenMP thread affinity information into a
buffer using the format specification provided.

Format
                                                  C / C++
size_t omp_capture_affinity(
char *buffer,
size_t size,
const char *format
);
                                                  C / C++
                                                  Fortran
integer function omp_capture_affinity(buffer,format)
character(len=*),intent(out) :: buffer
character(len=*),intent(in) :: format
                                                  Fortran
Binding
The binding thread set for an omp_capture_affinity region is the encountering thread.

Effect
                                                  C / C++
The omp_capture_affinity routine returns the number of characters in the entire thread
affinity information string excluding the terminating null byte (’\0’). If size is non-zero, it writes
the thread affinity information of the current thread in the format specified by the format argument
into the character string buffer followed by a null byte. If the return value is larger or equal to
size, the thread affinity information string is truncated, with the terminating null byte stored to
buffer[size-1]. If size is zero, nothing is stored and buffer may be NULL. If the format is NULL
or a zero-length string, the value of the affinity-format-var ICV is used.
                                                  C / C++

                                                        Fortran
The omp_capture_affinity routine returns the number of characters required to hold the
entire thread affinity information string and prints the thread affinity information of the current
thread into the character string buffer with the size of len(buffer) in the format specified by
the format argument. If the format is a zero-length string, the value of the affinity-format-var ICV
is used. If the return value is larger than len(buffer), the thread affinity information string is
truncated. If the format is a zero-length string, the value of the affinity-format-var ICV is used.
                                                        Fortran
If the format argument does not conform to the specified format then the result is implementation
defined.

Cross References
• affinity-format-var ICV, see Table 2.1
