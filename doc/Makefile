all: pipeline-tools.png makefile-dependencies.png


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<

makefile-dependencies.dot: makefile-dependencies-format.dot \
						   makefile-dependencies-specify-inputs.dot
	cat makefile-dependencies-format.dot > makefile-dependencies.dot
	cat makefile-dependencies-specify-inputs.dot >> makefile-dependencies.dot
	echo '}' >> makefile-dependencies.dot