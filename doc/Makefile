all: pipeline-tools.png \
	makefile-dependencies.png \
	makefile-specify-inputs.png \
	makefile-clean-ott.png \
	makefile-clean-phylo.png \
	makefile-subproblems.png


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<

makefile-dependencies.dot: makefile-format.dot \
						   makefile-specify-inputs.txt \
						   makefile-clean-ott.txt \
						   makefile-clean-phylo.txt \
						   makefile-subproblems.txt 
	cat makefile-format.dot > $@
	cat makefile-specify-inputs.txt >> $@
	cat makefile-clean-ott.txt >> $@
	cat makefile-clean-phylo.txt >> $@
	echo '}' >> $@


%.dot: makefile-format.dot %.txt
	cat makefile-format.dot > $@
	cat $*.txt >> $@
	echo '}' >> $@