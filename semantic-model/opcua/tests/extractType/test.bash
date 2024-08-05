CORE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Schema/Opc.Ua.NodeSet2.xml
RESULT=result.ttl
NODESET2OWL_RESULT=nodeset2owl_result.ttl
CORE_RESULT=core.ttl
CLEANED=cleaned.ttl
NODESET2OWL=../../nodeset2owl.py
EXTRACTTYPE=../../extractType.py
DEBUG=true
if [ "$DEBUG"="true" ]; then
    DEBUG_CMDLINE="-m debugpy --listen 5678"
fi
TESTNODESETS=(test_object_types.NodeSet2)
CLEANGRAPH=cleangraph.py

echo Prepare core nodeset
echo -------------------------
python3 ${NODESET2OWL} ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${CORE_RESULT}

echo Starting Feature Tests
echo --------------------------------
for nodeset in "${TESTNODESETS[@]}"; do
    echo test $nodeset
    if [ "$DEBUG"="true" ]; then
        echo DEBUG: python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT}
    fi
    python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT}
    python3 ${EXTRACTTYPE}
    #diff ${nodeset}.ttl ${RESULT} || exit 1
done
