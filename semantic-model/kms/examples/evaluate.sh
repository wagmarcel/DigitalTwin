#!/bin/bash

TOOLPREFIX=../../shacl2flink
OUTPUTDIR=output
SHACL=shacl.ttl
QUOTE="'"
PYTHON=python3
KNOWLEDGE="${OUTPUTDIR}/knowledge.ttl"
SQLITEDB=${OUTPUTDIR}/database.db
SQLITE3=sqlite3
sqlite_files="${OUTPUTDIR}/core.sqlite ${OUTPUTDIR}/ngsild.sqlite ${OUTPUTDIR}/rdf.sqlite ${OUTPUTDIR}/ngsild-models.sqlite ${OUTPUTDIR}/shacl-validation.sqlite"

evaluate() {
    MODEL=$1
    ${PYTHON} ${TOOLPREFIX}/create_rdf_table.py ${KNOWLEDGE}
    ${PYTHON} ${TOOLPREFIX}/create_core_tables.py
    ${PYTHON} ${TOOLPREFIX}/create_udfs.py
    ${PYTHON} ${TOOLPREFIX}/create_ngsild_tables.py ${OUTPUTDIR}/${SHACL}
    ${PYTHON} ${TOOLPREFIX}/create_ngsild_models.py ${OUTPUTDIR}/${SHACL} ${KNOWLEDGE} ${MODEL}
    ${PYTHON} ${TOOLPREFIX}/create_sql_checks_from_shacl.py ${OUTPUTDIR}/${SHACL} ${KNOWLEDGE}
}

get_results() {
    cat ${sqlite_files} | ${SQLITE3} ${SQLITEDB}
    echo 'select * from alerts_bulk;'| sqlite3 ${SQLITEDB}

}

files="$@"
if [ -z "$files" ]; then
    files=$(ls example*.yaml)
fi
for file in $files; do
    echo ----------------------------------
    echo ----------------------------------
    echo Testing file $file
    echo ----------------------------------
    echo ----------------------------------
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}

    touch ${OUTPUTDIR}/knowledge.ttl
    eval $(echo "yq ${QUOTE}.\"${SHACL}\"${QUOTE}" ${file}) > ${OUTPUTDIR}/${SHACL}
    fields=$(yq eval 'keys | .[] ' example1.yaml)
    for field in $fields; do
        if [[ "$field" =~ model* ]]; then
            echo -----------------------
            echo Processing $field
            echo -----------------------
            eval $(echo "yq ${QUOTE}.\"${field}\"${QUOTE}" ${file}) > ${OUTPUTDIR}/${field}
            evaluate "${OUTPUTDIR}/$field"
            get_results
            if [ ! -z "$DEBUG" ]; then
                echo "Do you wish to continue?"
                    select yn in "Yes" "No"; do
                        case $yn in
                            Yes ) break;;
                            No ) exit;;
                        esac
                    done
            fi
        fi
    done
done