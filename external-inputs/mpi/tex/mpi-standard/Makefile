ALL: all-redirect

# Makefile for MPI-Report...
# by Rainer Keller @ HLRS
# Updated by William Gropp @ UIUC
#
# WARNING: This makefile uses GNU extensions to the make language and
# extensions to grep
#
# Use
#   make           to produce version based on the interpreter (ps or pdf)
#   make clean     to get rid of most generated, intermediate files
#   make veryclean to get rid of everything which can be reproduced
#   make distclean to get rid of the final files as well.
#
#   make instr.pdf to get the instructions document
#
# To produce a final version of the standard, refer first to instr.pdf .
# Ensure that \draftfalse is set in mpi-report.tex

# Programs
LATEX=pdflatex -halt-on-error
TOHTML=tohtml
GNUPLOT_BIN=gnuplot
RM=rm -fr

MAIN=mpi-report
BIB_FILE=refs.bib

TEX      := $(shell ls -1 chap-*/[a-zA-Z]*.tex  ./app*.tex $(MAIN).tex)
TEXNOAPPLANG := $(shell ls -1 chap-*/[a-zA-Z]*.tex $(MAIN).tex)
PDFINFO  := $(shell which pdfinfo)
# mapnames is part of sowing; see
# http://wgropp.cs.illinois.edu/projects/software/sowing/
# This is used only to provide links from the use of an MPI name to
# its definition, particularly in the language bindings.  If mapnames
# is not present, the standard will be built without these links
MAPNAMES := $(shell which mapnames)

# Generated appLang files - this includes Fortran 2008 but leaves out
# the now-removed C++ files
APPLANG_GEN = appLang-CNames.tex appLang-FNames.tex appLang-F2008Names.tex

# Version number for the current version of the MPI standard
MPIVERSION=5.1
# MPIVERSIONSHORT is the version, with no non-digits. Used in creating
# version-specific filenames
MPIVERSIONSHORT=51

RENDERED_FILES = \
        chap-abi/abi-rendered.tex \
        chap-binding/binding-2-rendered.tex \
        chap-coll/coll-rendered.tex \
        chap-context/context-rendered.tex \
        chap-datatypes/datatypes-rendered.tex \
        chap-deprecated/deprecated-rendered.tex \
        chap-dynamic/dynamic-2-rendered.tex \
        chap-ei/ei-2-rendered.tex \
        chap-inquiry/inquiry-rendered.tex \
        chap-io/io-2-rendered.tex \
        chap-misc/misc-2-rendered.tex \
        chap-one-side/one-side-2-rendered.tex \
        chap-pt2pt/pt2pt-rendered.tex \
        chap-part/part-rendered.tex \
		chap-tools/tools-3-rendered.tex \
        chap-ft/ft-rendered.tex \
        chap-tools/mpit-rendered.tex \
        chap-tools/prof-rendered.tex \
        chap-topol/topol-rendered.tex \
        chap-appLang/appLang-Const-rendered.tex

all-redirect: cleanversions

# Remove any old toc - if there were problems in a previous run, they
# can contaminate the toc file
# A previous version had a potentially infinite loop to rerun if there
# was a message from Latex saying "Rerun to get" - but it looked in the
# wrong file, and hence failed to run LATEX enough times. This version
# is aware of the interactions between each run and does only as many
# as necessary
#
# A special case is handling of the indices.  This must be integrated with
# the creation of the $(MAIN).idx file.
# So, there are four passes over the LaTeX file; these are needed because
# each of the passes may create slight changes in the pagination
#   Pass 1: Create $(MAIN).aux, needed for bibtex to create citations.
#   Pass 2: Create $(MAIN).idx, needed for buildindices to create the
#           indices with the correct page numbers (which must come after
#           the bibliography and cross-references are handled)
#   Pass 3: Integrate the indices into the document and, if mapnames is
#           available, update the binding references with hyperlinks back
#           to the function definitions.
#   Pass 4: Process the labels that go with the indices
# (previous versions of this Makefile created each file, such as the
# indices or the bib, through a separate step, leading to even more passes
# over the input files)
#	./buildindices --newexamples --lognomain nomain.txt \
#		--warnfile warnindex.txt
# Add --warndupmain for more warnings on indices
# Add --constfile --printnolist --constfile maint/cnstlist.txt to generate
# Uses --noexampleindex=number to turn off the addition of "Example x.x: ..."
# to the example index, because they are included in the list of examples
# lists of the constants; this can also show constants that are used with
# the wrong macro, e.g., datatypes with \mpiconst
$(MAIN).pdf: $(APPLANG_GEN) $(TEX) buildindices
	@rm -f $(MAIN).toc $(MAIN).check $(MAIN).aux $(MAIN).idx $(MAIN).mel
	@echo "---- Running $(LATEX) $(MAIN).tex ---"
	@echo "% empty" > func-index.tex
	$(LATEX) $(MAIN).tex
	bibtex $(MAIN)
	$(LATEX) $(MAIN)
	@rm -f nomain.txt warnindex.txt
	./buildindices2 --idxfile mpi-report.idx --lognomain nomain.txt \
		--noexampleindex=number \
		--warnfile warnindex.txt
	$(MAKE) bindinglinks
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

$(APPLANG_GEN): $(TEXNOAPPLANG) buildapplang
	./buildapplang

#
# Create the document that describes how to edit the document
# Run twice in case needed to resolve references
instr.pdf: instr.tex
	$(LATEX) instr
	$(LATEX) instr

#
# Provide rules for creating the figure graphics from the figure source
# files.  Note that these require two tools, fig2dev and esptopdf, that
# many users do not have installed on their systems
FIG2DEV  = fig2dev
EPSTOPDF = epstopdf
%.eps: %.fig
	$(FIG2DEV) -L eps $< $@

%.eepic: %.fig
	$(FIG2DEV) -L eepic $< $@

%.pdf: %.fig
	$(FIG2DEV) -L pdftex -p 1 $< $@

%.pdf: %.eps
	$(EPSTOPDF) --outfile=$@ $<

%.pdf: %.ps
	$(EPSTOPDF) --outfile=$@ $<

# Look for common errors in the LaTeX build. If there are messages, include
# the chapter file name to help localize the message.
# Note that errorsum will exit with return status 1 if it finds something.
errorsummary: mpi-report.log
	./errorsum --noexindex
	@if test -s warnindex.txt ; then \
	    echo "Warnings from buildindices:" ; \
	    cat warnindex.txt ; fi
#
# Also remove all chapter pdf and chappage files
clean:
	$(RM) $(shell find . -name '*.aux' -print)
	$(RM) $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).brf $(MAIN).dvi $(MAIN).glo $(MAIN).gls $(MAIN).idx $(MAIN).idx.save $(MAIN).ilg $(MAIN).ind $(MAIN).lof $(MAIN).log $(MAIN).lot $(MAIN).out $(MAIN).toc tmp.txt $(MAIN).idx.all $(MAIN).mel
	$(RM) const.idx const.ind decls.idx decls.ind examples.idx examples.ind
	$(RM) mpifunction.idx mpifunction.ind term.idx term.ind typedef.idx
	$(RM) typedef.ind mkindex.log nomain.txt warnindex.txt *.ilg mapconst.cit
	$(RM) -f instr.out
	$(RM) -f chappage.txt chap-*/chappage.txt
	$(RM) -f chap-*/*.pdf
	find . \( -not -type d \) -and \
	  \( -name 'ex.out' -o -name 'ex[0-9]*.[ocCf]' -o -name 'ex[0-9]*.f90' \) -print | xargs $(RM)
	for dir in `find . -name 'chap-*' -type d -maxdepth 1 -print` ; do \
	    ( cd $$dir && $(MAKE) clean ) ; \
	done

veryclean: clean
	find . \( -not -type d \) -and \
	  \( -name '*~' -o -name '*.aux' -o -name '*.bak' -o -name '#*#' -o -name '*.fitlog' -o -name 'ex.out' -o -name 'ex[0-9]*.[ocCf]' -o -name 'ex[0-9]*.f90' \) -print | xargs $(RM)
	$(RM) temp

# Note that func-index.tex $(APPLANG_GEN) are generated files
distclean maintainer-clean: veryclean
	$(RM) $(MAIN).pdf $(MAIN).pdf.gz $(MAIN).pdf.bz2 $(MAIN).ps $(MAIN)_tmp.ps $(MAIN).ps.gz $(MAIN).ps.bz2 $(MAIN)-small.ps $(MAIN)-small-duplex.ps $(MAIN)-twice.ps $(MAIN)-split-book-A5.ps
	$(RM) func-index.tex $(APPLANG_GEN)

#
# Check the example programs.
# A few LaTeX files include the rendered files. Make sure that they are
# present.
check: mpicompilechk/mpichk $(RENDERED_FILES)
	for dir in `find . -maxdepth 1 -name 'chap-*' -type d -print` ; do \
	    echo "Checking examples in $$dir" ; \
	    file=`(cd $$dir && make -s chapfiles)`; \
	    ./mpicompilechk/mpichk --outdir=$$dir $$dir/$$file.tex ; \
	done

# getlatex checks for LaTeX usage
# The first grep line looks for mpibind declarations that are missing a tie (~)
# between types and argument names, e.g., const~MPI\_Aint sdispls[]
# The second grep line looks for naked LaTeX commands in section titles, which
# can cause problems for the PDF links.
# This check is less strict to encourage more use.  The goal should be to
# use ./getlatex chap-*/*.tex , e.g., warn about both pageref and punctuation
# of quotes
checklatex: getlatex
	@files=`echo "$(wildcard chap-*/*.tex)" \
	| sed -e 's%chap-[-A-Za-z]*/[-A-Za-z0-9]*-rendered\.tex%%g' \
	| sed -e 's%[-A-Za-z]*/temp[-A-Za-z0-9]*\.tex%%g'` ;\
	for file in $$files ; do \
	    ./getlatex --allowpageref --noquotechk --noeolspacechk $$file ;\
	    if grep 'mpibind{' $$file | grep '[A-Za-z] [A-Za-z]' >/dev/null ; then \
	        echo "$$file : mpibind missing tie :" ; \
	        grep 'mpibind{' $$file | grep '[A-Za-z] [A-Za-z]' ; \
	    fi ; \
	    if grep 'section{' $$file | sed -e 's/.*section{//g' | sed -e 's/\\texorpdfstring{.*}//g' | sed -e 's/\\#//g' | sed -e 's/\\ //g' -e 's/\\_/_/g' | grep '\\' > /dev/null ; then \
	        echo "$$file : section with unprotected LaTeX command :" ; \
		grep 'section{' $$file | sed -e 's/.*section{//g' | sed -e 's/\\texorpdfstring{.*}//g' | sed -e 's/\\#//g' | sed -e 's/\\ //g' -e 's/\\_/_/g' | grep '\\' ; \
	    fi ;\
	done

# Allow people to override the default location of Python, if necessary.
PYTHON := python3

pythoncheck:
	@$(PYTHON) -m pip install --user -r requirements-test.txt > /dev/null
	@$(PYTHON) -m pytest -p no:pytest-sugar -p no:pytest-tdlr -p no:pytest-azurepipelines -q --tb=line

#
# Create the single chapter versions of the document
# These simplify checks for index and bibliographic entries
eachchap:
	for dir in `find . -name 'chap-*' -type d -maxdepth 1 -print` ; do \
	    echo "Building chapter PDF in $$dir" ; \
	    ( cd $$dir && $(MAKE) ) ; \
	done

#
# The following targets produce specific versions of the document.
# For the versions that do not include extra text, but that
# change the appearence slightly through color, we save the func-index.tex
# as func-index-<version>.tex.  These provide a way to confirm that the
# pagination is the same (it isn't a certain test, but a failure to compare
# does indicate an error).

ifdef V
BINDING_TOOL_VERBOSE := --log INFO
else
BINDING_TOOL_VERBOSE :=
endif

# Default to rendering in the embiggened style
BINDING_RENDER_VERSION := 4.1
BINDING_RENDER_DEFAULT := 41

APIS_FILE := apis.json

# FIXME: This kinda sucks -- it doesn't take dependencies into account
# (i.e., it always re-renders everything, regardless of whether source
# files have changed or not).  Should probably update this to be a
# rule of some flavor so that we only get re-rendering when it is
# needed.

binding-prepass:
	@$(PYTHON) binding-tool/binding_prepass.py ./ $(APIS_FILE)

rendered: binding-prepass
	@for file in $(RENDERED_FILES); do \
	    rm -f $$file; \
	    orig=`echo $$file | sed -e s/-rendered//`; \
	    echo "RENDERING: $$orig --> $$file"; \
	    $(PYTHON) binding-tool/binding_emitter.py $(BINDING_TOOL_VERBOSE) $(APIS_FILE) $$orig > $$file; \
	    if test $$? -ne 0; then \
	      echo '*** ERROR: MPI API binding rendering failed'; \
	      echo '*** Run with "make V=1" to see more info'; \
	      exit 1; \
	    fi; \
	done


$(APIS_FILE): $(RENDERED_FILES:%-rendered.tex=%.tex)
	$(PYTHON) binding-tool/binding_prepass.py ./ apis-tmp
	if cmp -s apis-tmp $(APIS_FILE) ; then rm -f apis-tmp ; \
	else mv apis-tmp $(APIS_FILE) ; fi

%-rendered.tex: %.tex $(APIS_FILE)
	rm -f $@
	@echo "RENDERING: $< --> $@"
	$(PYTHON) binding-tool/binding_emitter.py $(BINDING_TOOL_VERBOSE) \
		$(APIS_FILE) $< > $@


#
# Produce a clean version of the standard.  By clean, we mean one without
# any markup about the changes in the standard.
MAIN_GENFILES = mpi-report.toc mpi-report.aux func-index.tex

#cleandoc: rendered
cleandoc: $(RENDERED_FILES) mpi-report.tex mpi-user-macs.tex mpi-sys-macs.tex
	$(MAKE) cleandoc-backend

cleandoc-backend:
	$(MAKE) mpi-report.pdf
	mv -f func-index.tex func-index-clean.tex

# Book printing requires setting some values in mpi-report.tex.
# At one point, this was done by reading a configuration file, but
# we've opted for a simpler approach, now that there is only one version
# (as opposed to versions with different sort of change markers)
bookprintingdoc: rendered
	$(MAKE) mpi-report.pdf
	mv -f func-index.tex func-index-book.tex

#
# Here are the versions for MPI 4.1.
# If creating multiple versions, consider comparing func-index-clean.tex
# for each version.  They should be the same if the documents are the same,
# since the index contains explicit page numbers (this is a necessary but not
# sufficient condition for the documents to be the same (in some sense), and
# in practice, often exposed problems)
cleanversions:
	-rm -f $(APPLANG_GEN)
	$(MAKE) cleandoc
	mv mpi-report.pdf mpi$(MPIVERSIONSHORT)-report.pdf

TOHTML_ARGS = -default -numbers -dosnl -htables -quietlatex -allgif \
	-endpage mpi5-forum-tail.htm -Wnoredef --mpidoc \
	--latexpgm pdflatex --indexfile mpi$(MPIVERSIONSHORT)-report-html.idx \
	--lstlisting
# For debugging the latex images, add: --latex-leavetmp  --latexcmds
# Removed --indexname myindex because we need to process the indices separately

HTMLVERSION:
	@if [ ! -f mpi-report.bbl ] ; then \
	     echo "No mpi-report.bbl available.  Use make cleandoc and rerun" ;\
	     exit 1; \
	fi
	echo "%empty" > general-html.tex
	cp general-html.tex examples-html.tex
	cp general-html.tex const-html.tex
	cp general-html.tex decls-html.tex
	cp general-html.tex typedef-html.tex
	cp general-html.tex funcdef-html.tex
	cp mpi-report.bbl mpi-reporthtml.bbl
	rm -f mpi-reporthtml.tex
	sed -e '/DraftwatermarkOptions/d' -e '/\\overfullrule/d' \
	     -e '/draftwatermark/d' -e '/\\drafttext/d' \
		mpi-report.tex > mpi-reporthtml.tex
	export TOHTML_LATEX="$(LATEX)" && $(TOHTML) $(TOHTML_ARGS) -basedef mpi5defs.txt -o mpi$(MPIVERSIONSHORT)-report.tex mpi-reporthtml.tex
	rm -f m.idx m1.idx
	./cleanidx --inputfile mpi$(MPIVERSIONSHORT)-report-html.idx \
		--outputfile m.idx
	./bindex --idxname CONST \
		--idxfile m.idx \
		--outfile const-html.tex --remainder m1.idx
	./bindex --idxname EXAMPLES \
		 --idxfile m1.idx \
		--outfile examples-html.tex --remainder m.idx
	./bindex --idxname TYPEDEF \
		 --idxfile m.idx \
		--outfile typedef-html.tex --remainder m1.idx
	./bindex --idxname TERM \
		 --idxfile m1.idx \
		--outfile general-html.tex --remainder m.idx
	./bindex --hasidxname \
		 --idxfile m.idx \
		--outfile funcdef-html.tex --remainder m1.idx
	export TOHTML_LATEX="$(LATEX)" && $(TOHTML) $(TOHTML_ARGS) -basedef mpi5defs.txt -o mpi$(MPIVERSIONSHORT)-report.tex mpi-reporthtml.tex
	rm -f mpi-reporthtml.tex

cleanhtml:
	-rm -f img[0-9]*.tex img[0-9]*.ler mpi*.ler mpi*.hux latex.err
	-rm -f const-html.tex decls-html.tex examples-html.tex \
		funcdef-html.tex general-html.tex typedef-html.tex \
		mpi-reporthtml.tex mpi-reporthtml.bbl \
		mpi$(MPIVERSIONSHORT)-report-html.idx m.idx m1.idx

# ------------------
# Special code to update the language bindings
# This requires a special program from the sowing package; this is an old
# hack that despite being ugly, is useful.
# This step is run after the execution of buildapplang. It cannot be
# separated from that step because the pythonization stage updates files that
# are input dependencies for the buildapplang step, and hence its output
# will be overwritten by buildapplang
#
# If mapnames is not available, this target does nothing (this turns
# routine references in the language binding appendix into hyperlinks to the
# function definition within the standard.  Without this step, there is no
# change to the text.  If there are any problems with this step, set
# MAPNAMES to the empty string.
bindinglinks: mpi-report.idx indextomap.pl $(APPLANG_GEN)
	if [ -n "$(MAPNAMES)" -a -x "$(MAPNAMES)" ] ; then \
	    ./indextomap.pl -nofunc mpi-report.idx > mapconst.cit ; \
	    cat appLang-CNames.tex | $(MAPNAMES) -map mapconst.cit -latexout \
	        -backslashalpha -latexcmd \\hyperlink > cidx.tex ; \
	    cat appLang-FNames.tex | $(MAPNAMES) -map mapconst.cit -latexout \
	        -backslashalpha -latexcmd \\hyperlink > fidx.tex ; \
	    cat appLang-F2008Names.tex | $(MAPNAMES) -map mapconst.cit -latexout \
	        -backslashalpha -latexcmd \\hyperlink > f08idx.tex ; \
	    mv cidx.tex appLang-CNames.tex ; \
	    mv fidx.tex appLang-FNames.tex ; \
	    mv f08idx.tex appLang-F2008Names.tex ; \
	fi

.PHONY: rendered binding-prepass cleanversions clean veryclean bindinglinks all-redirect cleandoc cleandoc-backend book distclean maintainer-clean check eachchap bookprintingdoc HTMLVERSION checklatex pythoncheck
