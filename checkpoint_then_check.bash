#!/bin/bash
set -x
cfg_fn="${1}"
out_dir="${2}"
out_tag="${3}"
num_cores="${4}"
status_fn=".STATUS.txt"
redirect_fn="REDIRECT.txt"
pipeline_notes_fn="PIPELINE_NOTES.txt"
check_filename="checksum_for_run.md5"

if test -z $num_cores ; then
    num_cores=8
fi

if ! test -f "${cfg_fn}" ; then
    echo "Expecting snakemake configfile as first argument, but \"${cfg_fn}\" does not exist."
    exit 1
fi
full_out_dir="${out_dir}/${out_tag}"
if ! test -d "${out_dir}" ; then
    mkdir "${out_dir}" || exit
fi
if test -d "${full_out_dir}" ; then
    echo "\"${full_out_dir}\" is in the way"
    exit 1
fi
mkdir "${full_out_dir}" || exit
status_fp="${full_out_dir}/${status_fn}"
echo "CHECKPOINTING" > "${status_fp}"

if ! snakemake --configfile "${cfg_fn}" --directory="${full_out_dir}" --cores "${num_cores}" prechecksum_inputs ; then
    echo 'ERROR_IN_PRECHECKPOINTING' > "${status_fp}"
    exit 2
fi

if ! snakemake --configfile "${cfg_fn}" --directory="${full_out_dir}" --cores "${num_cores}" checksum_inputs ; then
    echo 'ERROR_IN_CHECKPOINTING' > "${status_fp}"
    exit 2
fi

check_filepath="${full_out_dir}/${check_filename}"
if ! test -f "${check_filepath}" ; then
    echo "ERROR: snakemake checksum_inputs failed to make \"${check_filepath}\""
    echo 'ERROR_IN_CHECKPOINTING_OUT' > "${status_fp}"
    exit 1
fi

echo "CHECKING_FOR_DUP" > "${status_fp}"

req_md=`cat "${check_filepath}"`
# ASSUMES all relevant custom synth in same out_dir ...
num_matching=`cat "${out_dir}"/*/"${check_filename}" | grep "${req_md}" | wc -l`
if test ${num_matching} -lt 1 ; then
    echo "ERROR: something is rotten in Denmark, did not grep req_md in all children of parent!"
    echo 'ERROR_IN_CHECKING_FOR_DUP' > "${status_fp}"
    exit 1
elif test ${num_matching} -gt 1 ; then
    for other in "${out_dir}"/*/"${check_filename}" ; do
        if ! test "${other}" = "${check_filepath}" ; then
            if test `cat "${other}"` = "${req_md}" ; then
                other_dir=`dirname "${other}"`
                if test -f "${other_dir}/${status_fn}" ; then
                    ostat=`cat "${other_dir}/${status_fn}"`
                    if test "${ostat}" = "RUNNING" -o "${ostat}" = "ERROR_IN_RUNNING" -o "${ostat}" = "COMPLETED_SUCCESSFULLY" ; then
                        echo "${other_dir}" > "${full_out_dir}/${redirect_fn}"
                        echo 'REDIRECTED' > "${status_fp}"
                        exit 0
                    fi
                fi
            fi
        fi
    done
    echo "saw an ephemeral match to the md5sum, but couldn't find it again" >> "${full_out_dir}/${pipeline_notes_fn}"
fi

echo "RUNNING" > "${status_fp}"
if ! snakemake --configfile "${cfg_fn}" --directory="${full_out_dir}" --cores "${num_cores}" all ; then
    echo 'ERROR_IN_RUNNING' > "${status_fp}"
    exit 4
fi
echo 'COMPLETED_SUCCESSFULLY' > "${status_fp}"
