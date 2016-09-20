all: pipeline-tools.png makefile-dependencies.png


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<

makefile-dependencies.dot: makefile-dependencies-format.dot \
						   makefile-dependencies-inputs.dot