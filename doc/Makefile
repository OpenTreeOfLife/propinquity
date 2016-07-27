all: pipeline-tools.png makefile-dependencies.png todo.pdf


%.png : %.dot
	dot -Tpng -o$@ $<

%.pdf : %.dot
	dot -Tpdf -o$@ $<
