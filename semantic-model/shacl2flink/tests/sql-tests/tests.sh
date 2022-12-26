#!/bin/bash
OUTPUTDIR=output
TOOLDIR=$(cd ../..; echo $PWD)
KMS=kms
TESTOUT=testout
RESULT=result


for testdir in $(ls $KMS); do
    KNOWLEDGE=knowledge.ttl
    SHACL=shacl.ttl
    pushd .
    cd $KMS/$testdir
    mkdir -p $OUTPUTDIR 

    for model in $(ls model*.jsonld); do
        MODEL=$model
        DATABASE=$OUTPUTDIR/database.db
        rm -f ${DATABASE}
        echo -n "Test with model ${MODEL} in dir ${testdir} ..."
        #echo create sqlite scripts for model $model
        #echo ------------------------------------------------
        python3 $TOOLDIR/create_rdf_table.py ${KNOWLEDGE}
        python3 $TOOLDIR/create_core_tables.py
        python3 $TOOLDIR/create_ngsild_models.py  ${SHACL} ${KNOWLEDGE} ${MODEL}
        python3 $TOOLDIR/create_ngsild_tables.py ${SHACL}
        python3 $TOOLDIR/create_sql_checks_from_shacl.py ${SHACL} ${KNOWLEDGE}
        #echo applying sqlite scripts
        #echo -----------------------
        sqlite3 ${DATABASE} < $OUTPUTDIR/rdf.sqlite
        sqlite3 ${DATABASE} < $OUTPUTDIR/core.sqlite
        sqlite3 ${DATABASE} < $OUTPUTDIR/ngsild.sqlite
        sqlite3 ${DATABASE} < $OUTPUTDIR/ngsild-models.sqlite
        sqlite3 ${DATABASE} < $OUTPUTDIR/property-checks.sqlite
        echo "select resource, event, severity from alerts_bulk_view;" | sqlite3 -quote  -noheader ${DATABASE}| sort > ${OUTPUTDIR}/${MODEL}_${TESTOUT}
        diff ${OUTPUTDIR}/${MODEL}_${TESTOUT} ${MODEL}_${RESULT} || { echo "failed"; exit 1; }
        echo " ok"
    done;
    rm -rf $OUTPUTDIR
    popd
done;