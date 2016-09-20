all: pipeline-tools.png \
	makefile-dependencies.png


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<

makefile-dependencies.dot: makefile-format.dot \
						   makefile-specify-inputs.dot \
						   makefile-clean-ott.dot 
	cat makefile-format.dot > makefile-dependencies.dot
	cat makefile-specify-inputs.dot >> makefile-dependencies.dot
	cat makefile-clean-ott.dot >> makefile-dependencies.dot
	echo '}' >> makefile-dependencies.dot