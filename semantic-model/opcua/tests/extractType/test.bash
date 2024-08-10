CORE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Schema/Opc.Ua.NodeSet2.xml
RESULT=result.ttl
NODESET2OWL_RESULT=nodeset2owl_result.ttl
CORE_RESULT=core.ttl
CLEANED=cleaned.ttl
NODESET2OWL=../../nodeset2owl.py
DEBUG=true
if [ "$DEBUG"="true" ]; then
    DEBUG_CMDLINE="-m debugpy --listen 5678"
fi
#TESTNODESETS=(test_minimal_object.NodeSet2 test_object_types.NodeSet2)
TESTNODESETS=(test_minimal_object.NodeSet2)
CLEANGRAPH=cleangraph.py
TYPEURI=http://example.org/MinimalNodeset
TESTURI=http://test/
TESTURN=urn:test

EXTRACTTYPE="../../extractType.py  -t ${TYPEURI}/Object -n ${TESTURI} ${NODESET2OWL_RESULT} -i ${TESTURN}"

echo Prepare core nodeset
echo -------------------------
if [ "$DEBUG"="true" ]; then
echo DEBUG comdline: python3 -m debugpy --listen 5678 --wait-for-client ${NODESET2OWL} ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${CORE_RESULT}
fi
python3 ${NODESET2OWL} ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${CORE_RESULT} || exit 1

echo Starting Feature Tests
echo --------------------------------
for nodeset in "${TESTNODESETS[@]}"; do
    echo test $nodeset
    if [ "$DEBUG"="true" ]; then
        echo DEBUG: python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} ${CORE_RESULT} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT}
        echo DEBUG: python3 ${EXTRACTTYPE}
    fi
    python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} ${CORE_RESULT} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT} || exit 1
    python3 ${EXTRACTTYPE} || exit 1
    #diff ${nodeset}.ttl ${RESULT} || exit 1
done
