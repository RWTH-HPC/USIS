dnl
dnl Caching is usually WRONG for systems with cross-mounted file systems
dnl (the cache file may correspond to a different system).  Since configure
dnl is not on a performance-critical path, go for robustness over speed.
dnl
define([AC_CACHE_LOAD], )dnl
define([AC_CACHE_SAVE], )dnl
dnl
AC_INIT
AC_CONFIG_SRCDIR([mpichk.in])
AC_PREREQ([2.71])
dnl Eventually, add support for better caching
dnl PAC_ARG_CACHING
AC_ARG_ENABLE(mpi,
[--enable-mpi  - Turn on testing of MPI programs (default = enable)],
enable_mpi="$enableval",enable_mpi="yes")
AC_SUBST(enable_mpi)
dnl
AC_ARG_ENABLE(mpicompiles,
[--enable-mpicompilers - Use mpicc etc to test the programs (default = disable)],
enable_mpicompilers="$enableval",enable_mpicompilers="no")
AC_ARG_ENABLE(fortran,
[--enable-fortran - Enable compiling the Fortran programs. (default = enable)],
enable_fortran="$enableval",enable_fortran="yes")
AC_ARG_ENABLE(fortran-interface,
[--enable-fortran-interface - Enable checking for missing MPI Fortran interface definitions (default = disable)],
enable_fortran_interface="$enableval",enable_fortran_interface="no")

dnl     checks for programs
AC_PATH_PROGS(PERL5,perl5 perl)
#
# Find the "default" compilers.  We need to do this unconditionally because
# these autoconf commands *WILL NOT WORK CORRECTLY* if placed within a shell
# conditional (if branch).  Specifically, autoconf will *ASSUME* that the
# PROG_xx commands will be executed unconditionally - such as the determination
# of the extension used for object files.
#
AC_PROG_CC

# Get Fortran compiler and characteristics.
if test "$enable_fortran" = "yes" ; then
    AC_PROG_FC
    AC_FC_SRCEXT(f90)
    AC_FC_FREEFORM
    AC_FC_MODULE_EXTENSION
    AC_FC_MODULE_FLAG
    AC_FC_IMPLICIT_NONE
else
    FC=false
fi
AC_SUBST(FC_MODEXT)
AC_SUBST(FC_MODINC)

AC_SUBST(MPICC)
if test "$enable_mpicompilers" != "no" ; then
    AC_PATH_PROGS(MPICC,mpicc mpcc)
    AC_PATH_PROGS(MPIF77,mpif77 mpif90 mpxlf)
    AC_PATH_PROGS(MPIF90,mpif90 mpxlf90 mpifortran)
    AC_SUBST(FFLAGS)
    AC_SUBST(FCFLAGS)
fi

# Use MPICC if it is set.  Otherwise, setup our own compiler and header files
if test -z "$MPICC" ; then
    dnl Prefer gcc
    MPICC=$CC
fi
if test "$GCC" = "yes" ; then
    # -Wno-long-long suppresses complaints about "long long", which is not
    # an ANSI type.
    CFLAGS="$CFLAGS -ansi -pedantic -Wpointer-arith -Wall -Wstrict-prototypes -Wno-long-long"
    # Later versions of GCC seem to need these
    # C Standards include c99, c11, c17, c23 .
    CFLAGS="$CFLAGS -Wno-uninitialized -std=c17"
    # Note that icc doesn't understand -Wredundant-decls, but still
    # sets $GCC=yes.  Sigh.
    if test "`basename $CC`" = "icc" -o \
       "`$CC --version 2>&1 | grep Intel`" != "" ; then
       :
    else
       CFLAGS="$CFLAGS -Wredundant-decls"
    fi
fi
# -Werror-implicit-function-declaration

# We need to find the appropriate warning options for Fortran, to match
# those for GCC.
# For example, for gfortran, use
#   -fimplicit-none
# to discover undeclared variables (sometimes ok, as in implicit integer m,
# and sometimes an error, as in MPI_REAL (this has been found in long-used
# examples).
# gfortran also supports other options, such as -Wall
# In some tests, these options were used with gfortran:
#  -fimplicit-none -Wall -Wno-c-binding-type -fallow-argument-mismatch


# For gfortran, we have the option of adding strong checks
# To use this, the Fortran modules need to be improved
if test $enable_fortran_interface = "yes" ; then
    if test $ac_cv_fc_compiler_gnu = "yes" ; then
        FCFLAGS="$FCFLAGS -Wimplicit-interface -Wimplicit-procedure"
    fi
fi
#
# Could add a test that an undeclared variable causes a warning.
#
# f90 integer kinds (it is possible to find these automatically)
INT4=4
AC_SUBST(INT4)
INT8=4
AC_SUBST(INT8)
dnl     checks for library functions
dnl     checks for system services
dnl     miscellaneous
dnl This is special code to support MPI Fortran programs.
AC_SUBST(MPI_INCS)
AC_SUBST(MPI_MOD_INCS)
# Need to fix mpif incs
MPIF_INCS=.
AC_SUBST(MPIF_INCS)
#
# Provide a test to see if undefined functions generate errors - if not,
# warn the user
CC=$MPICC
AC_OBJEXT
if test "X$ac_objext" = "X" ; then
   AC_MSG_ERROR([Configure failed to set the internal variable ac_objext!!!])
fi
AC_MSG_CHECKING([whether undeclared functions cause errors])
AC_COMPILE_IFELSE([AC_LANG_PROGRAM([[]], [[int r = myfunction(1);]])],[pac_cv_undef_fails=no],[pac_cv_undef_fails=yes])
AC_MSG_RESULT($pac_cv_undef_fails)
if test "$pac_cv_undef_fails" = no ; then
   AC_MSG_WARN([The C compiler and compiler options do not cause an error when an undeclared function is used.  Consider setting MPICHK_CFLAGS with the necessary options to cause such cases to fail])
fi
#
AC_CONFIG_COMMANDS([default-1],[[chmod a+x mpichk]],[[]])
AC_CONFIG_FILES([mpichk Makefile fortran/Makefile fortran08/Makefile testing/Makefile])
AC_OUTPUT
