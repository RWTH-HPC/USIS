#! /usr/bin/perl -w
#
# Take the mpi-report.idx to a mapping of names to page.  This can be used
# with the "mapnames" program to modify text with URLS
%nameToURL = ();
$debug = 0;
$doconst = 1;
$dofunc = 1;

# Names of functions that appear as CONST in the mpi-report.idx file
%specialfuncnames = (
    'MPI\_DUP\_FN' => 1,
    'MPI\_NULL\_COPY\_FN' => 1,
    'MPI\_NULL\_DELETE\_FN' => 1,
    'MPI\_COMM\_DUP\_FN' => 1,
    'MPI\_COMM\_NULL\_COPY\_FN' => 1,
    'MPI\_COMM\_NULL\_DELETE\_FN' => 1,
    'MPI\_WIN\_DUP\_FN' => 1,
    'MPI\_WIN\_NULL\_COPY\_FN' => 1,
    'MPI\_WIN\_NULL\_DELETE\_FN' => 1,
    'MPI\_TYPE\_DUP\_FN' => 1,
    'MPI\_TYPE\_NULL\_COPY\_FN' => 1,
    'MPI\_TYPE\_NULL\_DELETE\_FN' => 1,
    'MPI\_CONVERSION\_FN\_NULL' => 1,
    'MPI\_CONVERSION\_FN\_NULL\_C' => 1,
    );

# Check command line for options
foreach $arg (@ARGV) {
    if ($arg =~ /-?-noconst/) {
	$doconst = 0;
    }
    elsif ($arg =~ /-?-nofunc/) {
	$dofunc = 0;
    }
    elsif (-s $arg) {
	$infile = $arg
    }
    else {
       print STDERR "Unrecognized argument $arg\n";
        exit(1);
    }
}

open(FD, "<$infile" ) or die "Could not open input file $infile";

while (<FD>) {
    if (/\\indexentry\{(.*)\}\{(.*)\}/) {
	$name      = $1;
	$page      = $2;
	$indexname = "DEFAULT";
	$pagetype  = "hyperpage";
	# Find index type.  Ignore EXAMPLES and TERM indices
	if ($name =~ /([A-Z]*):(.*)/) {
	    $indexname = $1;
	    $name      = $2;
	}
	if ($indexname eq "TERM" || $indexname eq "EXAMPLES") {
	    next;
	}
	# Ignore const and/or functions if requested
	if ($indexname eq "CONST" && $doconst != 1) {
	    next;
	}
	if (($indexname eq "DEFAULT" || $indexname eq "BCFUNCTION") && \
	    $dofunc != 1) {
	    next;
	}
	# Find indexpage type
	if ($name =~ /(.*)\|(.*)/) {
	    $name = $1;
	    $pagetype = $2;
	}
	# Correct for erroneous index entries for functions that include
	# the parameter list
	if ($name =~ /([^\(\)\s]*)\s*\([^\(\)]*\)/) {
	    $name = $1;
	}
	# If the entry has formatting for the name, strip that
	if ($name =~ /([^@]*)@.*/) {
	    $name = $1;
	}
	# Remove trailing spaces
	$name =~ s/\s+//;
	#print $pagetype . "\n";
	# Only include MPI Function and MPI Handle names in the index map file
	# (including all other terms can cause problems for the name mapping
	# program because some indexed names are too common)
	if ($name =~ /^MPI/ && $pagetype eq "hyperindexformat{\\uu}") {
	    if (defined($nameToURL{$name})) {
		if ($nameToURL{$name} != $page) {
		    print STDERR "Multiple primary definitions for $name\n";
		    # Use only the first definition
		}
		# Don't generate a second entry
		next;
	    }
	    if ($dofunc == 0 && defined($specialfuncnames{$name})) {
		# Skip these "const" functions
		#print STDERR "Skipping $name\n";
		next;
	    }

            # Skip special cases
	    # (Nothing for now)
	    $nameToURL{$name} = $page;
	    print "$name -> \\hyperref{$page}\n" if $debug;
	    $cname = lc($name);
	    if ($cname =~ /mpi\\_(.)(.*)/) {
		$cname = "MPI\\_" . uc($1) . $2;
	    }
	    print "doc:+$name++$name++++ignore+page.$page\n";
	    if ($indexname eq "DEFAULT" && $name ne $cname) {
		print "doc:+$cname++$cname++++ignore+page.$page\n";
	    }
	}
    }
    else {
	print STDERR "Unrecognized line: $_";
    }
}

close(FD);
