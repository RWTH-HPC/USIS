'''
Contains all regex patterns used for all matching throughout the
MPI Binding Tool.
'''

import re


# mpi binding regex pattern
MPI_BINDING_PATTERN = re.compile(r'\\begin\{mpi-binding\}\s'
                                 r'(.+?)\s'
                                 r'\\end\{mpi-binding\}\s',
                                 re.DOTALL | re.MULTILINE)


# LIS patterns
PATTERN_LIS_SINGLE_BINDING = re.compile(r'^(\\begin\{(funcdef)\}'
                                        r'\{\s*([\w\\]+?)\s*\(.+?'
                                        r'\\end\{funcdef\})',
                                        re.DOTALL | re.MULTILINE)
PATTERN_LIS_DOUBLE_BINDING = re.compile(r'^(\\begin\{(funcdef2)\}'
                                        r'\{\s*([\w\\]+?)\s*\(.+?'
                                        r'\\end\{funcdef2\})',
                                        re.DOTALL | re.MULTILINE)
PATTERN_LIS_NA_BINDING = re.compile(r'^(\\begin\{(funcdefna)\}'
                                    r'\{\s*([\w\\]+?)\s*\(.+?'
                                    r'\\end\{funcdefna\})',
                                    re.DOTALL | re.MULTILINE)

# C patterns
PATTERN_C_BINDING = re.compile(r'^(\\(mpibind)'
                               r'\{\s*([\w\\]+?)\s*\(.+?\})',
                               re.DOTALL | re.MULTILINE)

PATTERN_C_NOTINT_BINDING = re.compile(r'^(\\(mpibindnotint)'
                                      r'\{\s*(?:[ \w\\]+\s)?'
                                      r'\s*([\w\\]+?)\s*\(.+?\})',
                                      re.DOTALL | re.MULTILINE)

PATTERN_C_TYPEDEF_BINDING = re.compile(r'^(\\(mpitypedefbind)'
                                       r'\{\s*([\w\\]+?)\s*\(.+?\})',
                                       re.DOTALL | re.MULTILINE)

PATTERN_C_TYPEDEF_VOID_BINDING = re.compile(r'^(\\(mpitypedefbindvoid)'
                                            r'\{\s*([\w\\]+?)\s*\(.+?\})',
                                            re.DOTALL | re.MULTILINE)

PATTERN_C_TYPEDEF_EMPTY_BINDING = re.compile(r'^(\\(mpitypedefemptybind)'
                                             r'\{\s*([\w\\]+?)\s*\(.+?\})',
                                             re.DOTALL | re.MULTILINE)


# F08 patterns
PATTERN_F08_BINDING = re.compile(r'^(\\(mpifnewbind)'
                                 r'\{\s*(?:[ \w\\=()*<>]+\s)?'
                                 r'\s*([\w\\]+?)\s*\([ \w,\\]*\)\s*'
                                 r'(\\fargs).+?\})',
                                 re.DOTALL | re.MULTILINE)

PATTERN_F08_SUB_BINDING = re.compile(r'^(\\(mpifnewsubbind)'
                                     r'\{\s*([\w\\]+?)\s*\([ \w,\\]*\)\s*'
                                     r'(\\fargs).+?\})',
                                     re.DOTALL | re.MULTILINE)


# F90 patterns
PATTERN_F90_BINDING = re.compile(r'(\\(mpifbind)\{'
                                 r'\s*(?:[ \w\\=()*<>]+\s)?'
                                 r'([\w\\]+?)\s*\([ \w,\\]*\)\s*'
                                 r'\\fargs.+?\})',
                                 re.DOTALL | re.MULTILINE)

PATTERN_F90_SUB_BINDING = re.compile(r'^(\\(mpifsubbind)'
                                     r'\{\s*([\w\\]+?)\s*\([ \w,\\]*\)\s*'
                                     r'(\\fargs).+?\})',
                                     re.DOTALL | re.MULTILINE)
