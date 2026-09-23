all: all-redirect

.SUFFIXES:
.SUFFIXES: .pdf .ps .dvi

all-redirect: errata-50.pdf

errata-50.pdf: errata-50.tex mpi-user-macs.tex mpi-sys-macs.tex
	./MAKE-MPI-CHAPTER errata-50.tex

errata-50.html: errata-50.tex
	tohtml -default -split -1 -nocontents erratabuild.tex </dev/null
	mv erratabuild.html errata-50.html

errata-40.pdf: errata-40.tex mpi-user-macs.tex mpi-sys-macs.tex
	./MAKE-MPI-CHAPTER errata-40.tex

errata-40.html: errata-40.tex
	tohtml -default -split -1 -nocontents erratabuild.tex </dev/null
	mv erratabuild.html errata-40.html

errata-31.pdf: errata-31.tex mpi-user-macs.tex mpi-sys-macs.tex
	./MAKE-MPI-CHAPTER errata-31.tex

errata-31.html: errata-31.tex
	tohtml -default -split -1 -nocontents erratabuild.tex </dev/null
	mv erratabuild.html errata-31.html

mpi-user-macs.tex:
	ln -s ../mpi-user-macs.tex
mpi-sys-macs.tex:
	ln -s ../mpi-sys-macs.tex

# Install allows us to update the ballots without re-exporting the
# project.
INSTALL_FILES = errata-50.pdf errata-50.html Makefile
WEBDIR =
install: ${INSTALL_FILES}
	for file in ${INSTALL_FILES} ; do \
	cp -p $$file ${WEBDIR}/$$file ; done

clean:
	rm -f errata-50.log tempch.* tempch*.* *.aux
