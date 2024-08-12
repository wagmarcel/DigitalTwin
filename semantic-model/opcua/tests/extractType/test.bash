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
TESTNODESETS=(
    test_references_to_typedefinitions.NodeSet2,http://my.demo/AlphaType
    test_minimal_object.NodeSet2,http://example.org/MinimalNodeset/ObjectType 
    test_object_types.NodeSet2,http://my.demo/AlphaType
    )
#TESTNODESETS=(test_object_types.NodeSet2,http://my.demo/AlphaType )
CLEANGRAPH=cleangraph.py
TYPEURI=http://example.org/MinimalNodeset
TESTURI=http://test/
TESTURN=urn:test
SHACL=shacl.ttl
ENTITIES=entities.ttl
INSTANCES=instances.jsonld
SPARQLQUERY=query.py

EXTRACTTYPE="../../extractType.py"


function mydiff() {
    shouldsort="$2"
    echo "$1"
    result="$3"
    expected="$4"
    echo "expected <=> result"
    cat $result | sort | tr -d ";," > /tmp/result
    cat $expected | sort | tr -d ";," > /tmp/expected
    if [ "$shouldsort" = "true" ]; then
        diff -w /tmp/expected /tmp/result || exit 1
    else
        diff -w $expected $result || exit 1
    fi
    
    echo Done
}

function checkqueries() {
    echo "$1"
    
    # Correctly capture the list of query files into an array
    queries=()
    while IFS= read -r -d '' file; do
        queries+=("$file")
    done < <(find . -maxdepth 1 -name "$2.query[0-9]*" -print0)

    # Check if the array is empty
    if [ ${#queries[@]} -eq 0 ]; then
        echo "No queries found matching pattern $2.query[0-9]*"
        return 1
    fi
    for query in "${queries[@]}"; do
        echo "Executing query for entities $ENTITIES and query $query"
        result=$(python3 "${SPARQLQUERY}" "${ENTITIES}" "$query")
        
        if [ "$result" != "True" ]; then
            echo "Wrong result of query: ${result}."
            exit 1
        fi
    done
    
    echo "Done"
}


echo Prepare core nodeset
echo -------------------------
if [ "$DEBUG"="true" ]; then
echo DEBUG comdline: python3 -m debugpy --listen 5678 --wait-for-client ${NODESET2OWL} ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${CORE_RESULT}
fi
python3 ${NODESET2OWL} ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${CORE_RESULT} || exit 1

echo Starting Feature Tests
echo --------------------------------
for tuple in "${TESTNODESETS[@]}"; do IFS=","
    set -- $tuple;
    nodeset=$1
    instancetype=$2 
    echo test $nodeset with instancetype $instancetype
    if [ "$DEBUG"="true" ]; then
        echo DEBUG: python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} ${CORE_RESULT} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT}
        echo DEBUG: python3 ${EXTRACTTYPE} -t ${instancetype} -n ${TESTURI} ${NODESET2OWL_RESULT} -i ${TESTURN} 
    fi
    echo Create owl nodesets
    echo -------------------
    python3 ${NODESET2OWL} ${nodeset}.xml -i ${BASE_ONTOLOGY} ${CORE_RESULT} -v http://example.com/v0.1/UA/ -p test -o ${NODESET2OWL_RESULT} || exit 1
    echo Extract types and instances
    echo ---------------------------
    python3 ${EXTRACTTYPE} -t ${instancetype} -n ${TESTURI} ${NODESET2OWL_RESULT} -i ${TESTURN} || exit 1
    mydiff "Compare SHACL" true ${nodeset}.shacl ${SHACL}
    mydiff "Compare instances" true ${nodeset}.instances ${INSTANCES}
    checkqueries "Check basic entities structure" ${nodeset}
    #diff ${nodeset}.ttl ${RESULT} || exit 1
done
