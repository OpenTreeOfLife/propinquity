all: pipeline-tools.png \
	paper-pipeline-tools.png \
	makefile-dependencies.png \
	makefile-specify-inputs.png \
	makefile-clean-ott.png \
	makefile-clean-phylo.png \
	makefile-subproblems.png \
	makefile-regraft-and-label.png


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<

makefile-dependencies.dot: makefile-format.dot \
						   makefile-specify-inputs.txt \
						   makefile-clean-ott.txt \
						   makefile-clean-phylo.txt \
						   makefile-subproblems.txt \
						   makefile-regraft-and-label.txt \
						   makefile-docs.txt
	cat makefile-format.dot > $@
	cat makefile-specify-inputs.txt >> $@
	cat makefile-clean-ott.txt >> $@
	cat makefile-clean-phylo.txt >> $@
	cat makefile-subproblems.txt >> $@
	cat makefile-regraft-and-label.txt >> $@
	cat makefile-docs.txt >> $@
	echo '}' >> $@


%.dot: makefile-format.dot %.txt
	cat makefile-format.dot > $@
	cat $*.txt >> $@
	echo '}' >> $@
