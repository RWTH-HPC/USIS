#! /usr/bin/env perl -w

#use strict;

@files = ();

if (defined($ARGV[0])) {
    @files = @ARGV;
}
else {
    @files = split(/\n/,`ls -1 chap-*/*.tex`);
}

foreach my $file (@files) {
    my $str = "";
    # Read entire file as string to simplify matches across lines
    open( INFD, "<$file" );
    while (<INFD>) {
	$str .= $_;
    }
    close( INFD );

#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}const \}/const /g;
#    $str =~ s/\\protect\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}/$1/g;
#    $str =~ s/\\noindent\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}/\\noindent $1/g;
#
#    # Challenge: Whether this should eat the newline depends on the 
#    # precise context.  Normally, this is the correct approach, but in one
#    # case (within verbatim or Verbatim), we need to leave in the second
#    # newline.  To do that, we handle that case first
#    $str =~ s/call MPI_TYPE_COMMIT\(newarrtype, ierr\)\}\n\{\\relax\\color\{black\}\\relax\{\}\}\n/call MPI_TYPE_COMMIT(newarrtype, ierr)}\n\n/g;
#
#    # As above, there is a case where the end of the group has to be 
#    # handled specially.  In this case, it ends just before an 
#    # end{implementors}.  So we handle this case first
#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}\n\\end\{implementors\}/$1\\end{implementors}/g; 
#
#    $str =~ s/\n\{\\relax\\color\{black\}\\relax\{\}\}\n/\n/g;
#
#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}\n\n/$1\n\n/sg;

# GOOD TO HERE
    
#    $str =~ s/\\noindent\{\\relax\\color\{black\}\\relax\{\}([^{}]*\{[^{}]*\}[^{}]*)\}/\\noindent $1/sg;
#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}\n?([^{}]*\{[^{}]*\}[^{}]*)\}/$1/sg;

#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}\n/$1\n/g; #NEW

#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*)\}/$1/g;

    # Many {\relax\color{black}\relax{}something} where something has 0 or 1 {} pairs,
    # and is not empty.
#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]+)\}/$1/g;
#    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]+\{[^{}]+\}[^{}]*)\}/$1/g;
    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*\{[^{}]+\}[^{}]*)\}/$1/g;
    $str =~ s/\{\\relax\\color\{black\}\\relax\{\}([^{}]*\{[^{}]+\}[^{}]*\{[^{}]+\}[^{}]*)\}/$1/g;

#    $str =~ s/(\\cdeclindex\{[^{}]+\})\\relax\{\}%/$1%/g;
#    $str =~ s/C\\relax\{\}/C/g;
#    $str =~ s/(\\cdeclindex\{[^{}]+\})\{\\relax\\color\{black\}\\relax\{\}\}%/$1%/g;

    # Save the original
    if (! -s "$file.orig") { 
	rename $file, "$file.orig";
    }
    open( OUTFD, ">$file" );
    print OUTFD $str;
    close( INFD );
}
