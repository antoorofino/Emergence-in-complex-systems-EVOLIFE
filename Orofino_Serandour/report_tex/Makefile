OUTFILE=report
INFILE=Patron_Rapport
LATEXMK = latexmk -use-make -quiet -pdf -pdflatex="pdflatex -interaction=nonstopmode" -cd

.PHONY: pdf preview

pdf:
	@ $(LATEXMK) $(INFILE).tex && latexmk -c -cd $(INFILE).tex && mv $(INFILE).pdf ./$(OUTFILE).pdf

preview:
	@ $(LATEXMK) -pvc $(INFILE).tex && latexmk -C -cd $(INFILE).tex