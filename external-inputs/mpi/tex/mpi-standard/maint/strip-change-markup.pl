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

    my $pre = "";
    # Note that if an MPIdelete is alone on a line, a newline after 
    # MPIdelete acts as a space, not a newline.  If MPIdelete is not alone
    # on a line, then the newline is a newline.
    # Allow erroneous use of a newline after the second argument
    while ($str =~ /^(.*)\\MPIdelete{[^}]*}{[^}]*}\n?{(.*)/s) {
	$pre .= $1;
	$post = $2;
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		print STDERR "Panic in delete (file $file)!\n";
		print STDERR "Context: " . substr($pre,-40) . substr($post,0,40) .
		    "\n";
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = skipBalancedBrace( $post );
	if ($lastchar eq "\n") {
	    # handle the newline case described above
	    print "Found newline at end of pre in MPIdelete - removing one at end of delete\n";
	    #$str =~ s/^\n//;
	}
	$str = $pre . "\\relax{}" . $str;
	$pre = "";
    }
    $str = $pre . $str;

    while ($str =~ /^(.*)\\MPIdeletenc{[^}]*}{[^}]*}{(.*)/s) {
	$pre .= $1;
	$post = $2;
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		print STDERR "Panic in delete (file $file)!\n";
		print STDERR "Context: " . substr($pre,-40) . substr($post,0,40) .
		    "\n";
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = skipBalancedBrace( $post );
	if ($lastchar eq "\n") {
	    # handle the newline case described above
	    print "Found newline at end of pre in MPIdelete - removing one at end of delete\n";
	    #$str =~ s/^\n//;
	}
	$str = $pre . "\\relax{}" . $str;
	$pre = "";
    }
    $str = $pre . $str;

    $pre = "";
    while ($str =~ /^(.*)\\MPIupdate{[^}]*}{[^}]*}%?\n? ?{(.*)/s) {
	$pre .= $1;
	$post = $2;
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		print STDERR "Panic in update replacement (file $file)!\n";
		print STDERR "Context: " . substr($pre,-40) . substr($post,0,40) . 
		    "\n";
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = returnBalancedBrace( $post, "}" );
	$str = $pre . "{\\relax\\color{black}\\relax{}" . $str;
	$pre = "";
    }
    $str = $pre . $str;

    $pre = "";
    while ($str =~ /^(.*)\\MPIupdatenc{[^}]*}{[^}]*}\n? ?{(.*)/s) {
	$pre .= $1;
	$post = $2;
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		print STDERR "Panic in update replacement (file $file)!\n";
		print STDERR "Context: " . substr($pre,-40) . substr($post,0,40) . 
		    "\n";
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = returnBalancedBrace( $post, "}" );
	$str = $pre . "{\\relax\\color{black}\\relax{}" . $str;
	$pre = "";
    }
    $str = $pre . $str;

    # Replace must eat the 3rd arg then return the fourth
    $pre = "";
    while ($str =~/^(.*)\\MPIreplace{[^}]*}{[^}]*} ?\n? ?{(.*)/s) {
	$pre = $1;
	$post = $2;
	# Save context for error messages
	$context = substr $pre,-20;
	$context .= "\\MPIreplace{...}{...}" . substr $post, 0, 20;
	if (length($context) > 100) { print "Perl is broken, len = " . length($context) . "\n"; last; }
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = skipBalancedBrace( $post );
	# Note: Neither the newline nor space should be used, but some
	# of the source files had these errors, and we work around them
	if ($str =~ /^\n? ?{(.*)/s) {
	    $str = "{\\relax\\color{black}\\relax{}" . returnBalancedBrace( $1, "}" );
	}
	else {
	    print "Panic in MPIreplace - missing { for replacement arg at $context\n";
	}
	$str = $pre . $str;
    }

    # Replace must eat the 3rd arg then return the fourth
    $pre = "";
    while ($str =~/^(.*)\\MPIreplacenc{[^}]*}{[^}]*}\n? ?{(.*)/s) {
	$pre = $1;
	$post = $2;
	# Save context for error messages
	$context = substr $pre,-20;
	$context .= "\\MPIreplacenc{...}{...}" . substr $post, 0, 20;
	if (length($context) > 100) { print "Perl is broken, len = " . length($context) . "\n"; last; }
	# Check for a commented-out command.  Be extra careful about matching
	# a newline at the very end of the string
	$lastchar = substr($pre,-1);
	if ($lastchar ne "\n") {
	    if ($pre =~ /%[^\n]*$/) {
		# This is a commented-out command
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	    if ($pre =~ /% *[^\n]$/) {
		$str = $pre . "{" . $post;
		$pre = "";
		next;
	    }
	}
	$str = skipBalancedBrace( $post );
	# Note: Neither the newline nor space should be used, but some
	# of the source files had these errors, and we work around them
	if ($str =~ /^\n? ?{(.*)/s) {
	    $str = "{\\relax\\color{black}\\relax{}" . returnBalancedBrace( $1, "}" );
	}
	else {
	    print "Panic in MPIreplace - missing { for replacement arg at $context\n";
	}
	$str = $pre . $str;
    }

    # Remove MPIdeleteBegin...End.  Do this by changing the "end" to a 
    # special character unused in the LaTeX source, then match the begin to 
    # this special character.
    $str =~ s@\n\\MPIdeleteEnd[^\n]*@§\\relax@sg;
    $str =~ s@\n\\MPIdeleteBegin[^§]*§@\n\\relax{} @sg;

    # Begin/End versions.
    # Match with versions
    $str =~ s/\n\\MPIupdateBegin{[^{}]*}{[^{}]*}%*\n/\n\\relax\\relax\\color{black}\\relax\n/g;
    $str =~ s/\n\\MPIupdateEnd{[^{}]*}%*\n/\n\\color{black}\\relax\n/g;
    # Don't match the newlines or extra spaces
    $str =~ s/\\MPIupdateBegin{[^{}]*}{[^{}]*}/\\relax\\color{black}\\relax%EDIT-ME/g;
    $str =~ s/\\MPIupdateEnd{[^{}]*}/\\color{black}\\relax%EDIT-ME/g;

    # A few special cases
    # context.tex, inquiry.tex
    $str =~ s/\\MPIupdate\$3.0\^\$0.179\^\$return 0;\^/return 0;/g;
    # coll.tex
    $str =~ s/\\MPIupdate\$3.0\^\$0\^\$\|\^/|/g;
    # datatypes.tex
    $str =~ s/\\MPIreplace\$3.0\^\$0\^\$zzdisp\[1\] = MPI_BOTTOM;\^\$zzdisp\[1\] = \(MPI_Aint\)0;\^/zzdisp[1] = (MPI_Aint)0;/g;

    # coll.tex.  This is an error in the MPI-3.0 document (it also deletes
    # the next token, leaving MPI_EXSCAN in text font.
    $str =~ s/\\MPIdelete\{0\}\{and \}//;

    # Save the original
    if (! -s "$file.orig") { 
	rename $file, "$file.orig";
    }
    open( OUTFD, ">$file" );
    print OUTFD $str;
    close( INFD );
}

#
# Call after matching the first brace at the beginning.  
# Returns the string starting with the first character
# after the matching close brace
sub skipBalancedBrace 
{
    my $str = $_[0];
    # Remove balanced {} at head of $str
    my $bracecnt = 1;
    while ($bracecnt > 0) {
	if ($str =~ /^[^{}]*}(.*)/s) {
	    $bracecnt --;
	    $str = $1;
	}
	elsif ($str =~ /^[^{}]*{(.*)/s) {
	    $bracecnt ++;
	    $str = $1;
	}
	else {
	    print STDERR "Panic! No closing } in skipBalancedBrace (file $file)\n";
	    last;
	}
    }
    return $str;
}

# Call after matching the first brace at the beginning.  
# Returns the string consisting of the characters before the
# matching close brace, followed by the contents of the second 
# argument, followed by the characters after the close 
# brace.  All of the other open and close braces are preserved.
sub returnBalancedBrace
{
    my $str = $_[0];
    my $closeStr = $_[1];

    my $pre = "";
    # Remove balanced {} at head of $str
    my $bracecnt = 1;
    while ($bracecnt > 0) {
	if ($str =~ /^([^{}]*)}(.*)/s) {
	    $pre .= $1;
	    $bracecnt --;
	    if ($bracecnt != 0) { $pre .= "}"; }
	    $str = $2;
	}
	elsif ($str =~ /^([^{}]*{)(.*)/s) {
	    $pre .= $1;
	    $str = $2;
	    $bracecnt ++;
	}
	else {
	    print STDERR "Panic!  No closing brace in returnBalancedBrace (file $file)\n";
	    if (defined($context)) { print STDERR $context; }
	    last;
	}
    }
    return $pre . $closeStr . $str;
}
