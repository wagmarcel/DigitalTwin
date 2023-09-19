#!/bin/bash

TOOLPREFIX=../../shacl2flink
OUTPUTDIR=files
SHACL=shacl.ttl
QUOTE="'"
PYTHON=python3
KNOWLEDGE="${OUTPUTDIR}/knowledge.ttl"

evaluate() {
    MODEL=$1
    ${PYTHON} ${TOOLPREFIX}/create_rdf_table.py ${KNOWLEDGE}
    ${PYTHON} ${TOOLPREFIX}/create_core_tables.py
    ${PYTHON} ${TOOLPREFIX}/create_udfs.py
    ${PYTHON} ${TOOLPREFIX}/create_ngsild_tables.py ${OUTPUTDIR}/${SHACL}
    ${PYTHON} ${TOOLPREFIX}/create_ngsild_models.py ${OUTPUTDIR}/${SHACL} ${KNOWLEDGE} ${MODEL}
    ${PYTHON} ${TOOLPREFIX}/create_sql_checks_from_shacl.py ${OUTPUTDIR}/${SHACL} ${KNOWLEDGE}
}

rm -rf ${OUTPUTDIR}
mkdir -p ${OUTPUTDIR}

touch ${OUTPUTDIR}/knowledge.ttl
eval $(echo "yq ${QUOTE}.\"${SHACL}\"${QUOTE}" example1.yaml) > ${OUTPUTDIR}/${SHACL}
fields=$(yq eval 'keys | .[] ' example1.yaml)
for field in $fields; do
    echo $field
    if [[ "$field" =~ object* ]]; then
        echo $field hello
        eval $(echo "yq ${QUOTE}.\"${field}\"${QUOTE}" example1.yaml) > ${OUTPUTDIR}/${field}
        evaluate "${OUTPUTDIR}/$field"
    fi
done
