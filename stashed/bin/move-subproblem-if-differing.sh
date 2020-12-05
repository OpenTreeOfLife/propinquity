#!/bin/bash
# Expects:
#  move...sh src_dir dest_dir treefile_name_list_file
src_dir="$1"
dest_dir="$2"
sub_id_file="$3"
if ! test -d "${src_dir}"
then
    echo "${src_dir} is not a directory"
    exit 1
fi
if ! test -d "${dest_dir}"
then
    echo "${dest_dir} is not a directory"
    exit 1
fi
if ! test -f "${sub_id_file}"
then
    echo "${sub_id_file} is not a file"
    exit 1
fi
# Copy if a file is missing from the destination or the .md5 has different content
for st in $(cat $3)
do
    b=$(basename -s .tre "${st}")
    dt="${dest_dir}/${st}"
    dm="${dest_dir}/${b}.md5"
    dn="${dest_dir}/${b}-tree-names.txt"
    st="${src_dir}/${st}"
    sm="${src_dir}/${b}.md5"
    sn="${src_dir}/${b}-tree-names.txt"
    if test -f "${dt}" -a -f "${dm}" -a -f "${dn}"
    then
	# diff return 1 if files are different, but success/true is "0" for bash!
        if ! diff "${dm}" "${sm}" >/dev/null 2>&1
        then
#	    echo "moving ${st} (diff)"
            cp "${st}" "${dt}" || exit
            cp "${sn}" "${dn}" || exit
            cp "${sm}" "${dm}" || exit
#	else
#	    echo "leaving ${st} ${dm} ${sm} (diff)"
        fi
    else
#	echo "moving ${st}"
        cp "${st}" "${dt}" || exit
        cp "${sn}" "${dn}" || exit
        cp "${sm}" "${dm}" || exit
    fi
done
