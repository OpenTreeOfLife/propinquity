# Before running this, add "%\n" after every includegraphics command cuz its not that smart.
FIGURES=$(grep '{.*/' paper.tex | sed 's|.*{\(.*/.*\)}.*|\1|'| sed 's|\\lyxdot |.|' )

for figure in $FIGURES ; do
    filename="../${figure}"
    new_filename=$(echo $figure | sed 's|/|__|g')
    echo -e "\n\n'$figure' -> ${new_filename}"
    # If the lyx svg-to-pdf command is correctly set to do "--export-area-drawing", then regenerating pdfs is unnecessary.
    if [ -f "${filename}" ] ; then
	ln -s "$filename" "$new_filename"
    fi
    if [ -f "${filename}.svg" ] ; then
	ln -s "${filename}.svg" "${new_filename}.svg"
	inkscape "${new_filename}.svg" "--export-pdf=${new_filename}.pdf" --export-area-drawing
    else
	ln -s "${filename%.pdf}.pdf" "${new_filename%.pdf}.pdf"
    fi
done

