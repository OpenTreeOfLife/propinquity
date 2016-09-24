# Before running this, add "%\n" after every includegraphics command cuz its not that smart.
FIGURES=$(grep '{.*/' paper.tex | sed 's|.*{\(.*/.*\)}.*|\1|'| sed 's|\\lyxdot |.|' )

for figure in $FIGURES ; do
    filename="../${figure}"
    new_filename=$(echo $figure | sed 's|/|__|g')
    new_filename=${new_filename%%.pdf}.pdf
    echo "\n\n'$figure' -> ${new_filename}"
    # If the lyx svg-to-pdf command is correctly set to do "--export-area-drawing", then regenerating pdfs is unnecessary.
    if [ -f "${filename}.svg" ] ; then
	filename="${filename}.svg"
	inkscape "$filename" "--export-pdf=${new_filename}" --export-area-drawing
    else
	filename="${filename%.pdf}.pdf"
	cp "${filename}" "${new_filename}"
    fi
done

