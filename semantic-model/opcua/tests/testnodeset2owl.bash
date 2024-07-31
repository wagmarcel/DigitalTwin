
export CORE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Schema/Opc.Ua.NodeSet2.xml
export CORE_SERVICES_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Schema/Opc.Ua.NodeSet2.Services.xml
export DI_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/DI/Opc.Ua.Di.NodeSet2.xml
export PADIM_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/PADIM/Opc.Ua.PADIM.NodeSet2.xml
export DICTIONARY_IRDI=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/PADIM/Opc.Ua.IRDI.NodeSet2.xml
export IA_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/IA/Opc.Ua.IA.NodeSet2.xml
export MACHINERY_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Machinery/Opc.Ua.Machinery.NodeSet2.xml
export MACHINERY_PROCESSVALUES_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Machinery/ProcessValues/opc.ua.machinery.processvalues.xml
export MACHINERY_JOBS_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/ISA95-JOBCONTROL/opc.ua.isa95-jobcontrol.nodeset2.xml
export LASERSYSTEMS_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/LaserSystems/Opc.Ua.LaserSystems.NodeSet2.xml
export MACHINERY_EXAMPLE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Machinery/Opc.Ua.Machinery.Examples.NodeSet2.xml
export MACHINETOOL_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/MachineTool/Opc.Ua.MachineTool.NodeSet2.xml
export PUMPS_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Pumps/Opc.Ua.Pumps.NodeSet2.xml
export PUMP_EXAMPLE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Pumps/instanceexample.xml
export MACHINETOOL_EXAMPLE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/MachineTool/Machinetool-Example.xml
export LASERSYSTEMS_EXAMPLE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/LaserSystems/LaserSystem-Example.NodeSet2.xml
export BASE_ONTOLOGY=https://industryfusion.github.io/contexts/staging/ontology/v0.1/base.ttl
export PACKML_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/PackML/Opc.Ua.PackML.NodeSet2.xml
RESULT=result.ttl
CLEANED=cleaned.ttl
DEBUG=true
if [ "$DEBUG"="true" ]; then
    $DEBUG_CMDLINE="-m debugpy --listen 5678"
fi
TESTNODESETS=(test_object_types.NodeSet2 test_objects.NodeSet2 test_reference_reused.NodeSet2 test_references_special.NodeSet2)
CLEANGRAPH=cleangraph.py
echo Starting Feature Tests
echo -------------------------------- 
for nodeset in "${TESTNODESETS[@]}"; do
    echo test $nodeset
    if [ "$DEBUG"="true" ]; then
        echo DEBUG: python3 -m debugpy --listen 5678 --wait-for-client ../nodeset2owl.py ${nodeset}.xml -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p test -o ${RESULT}
    fi
    python3 ../nodeset2owl.py ${nodeset}.xml -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p test -o ${RESULT}
    diff ${nodeset}.ttl ${RESULT} || exit 1
done
echo Starting E2E specification tests
echo -------------------------------- 
comparewith=core_cleaned.ttl
echo Test ${CORE_NODESET}
python3 ../nodeset2owl.py ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o ${RESULT}
python3 $CLEANGRAPH $RESULT $CLEANED 
diff $CLEANED $comparewith || exit 1
nodeset=$DI_NODESET
comparewith=devices_cleaned.ttl
echo Test $DI_NODESET
echo Prepare core.ttl
python3 ../nodeset2owl.py ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o core.ttl
echo test devices
python3 ../nodeset2owl.py  ${DI_NODESET} -i ${BASE_ONTOLOGY} core.ttl -v http://example.com/v0.1/DI/ -p devices -o ${RESULT}
python3 $CLEANGRAPH $RESULT $CLEANED 
diff $CLEANED $comparewith  || exit 1
rm -f core.ttl
comparewith=machinery_cleaned.ttl
echo Test $MACHINERY_NODESET
echo Prepare core.ttl
python3 ../nodeset2owl.py ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o core.ttl
echo Prepare devices.ttl
python3 ../nodeset2owl.py  ${DI_NODESET} -i ${BASE_ONTOLOGY} core.ttl -v http://example.com/v0.1/DI/ -p devices -o devices.ttl
echo test machinery
python3 ../nodeset2owl.py ${MACHINERY_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl -v http://example.com/v0.1/Machinery/ -p machinery -o ${RESULT}
python3 $CLEANGRAPH $RESULT $CLEANED 
diff $CLEANED $comparewith  || exit 1
rm -f core.ttl device.ttl
comparewith=pumps_cleaned.ttl
echo Test $PUMPS_NODESET
echo Prepare core.ttl
python3 ${DEBUG_CMDLINE} ../nodeset2owl.py ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o core.ttl
echo Prepare devices.ttl
python3 ${DEBUG_CMDLINE} ../nodeset2owl.py  ${DI_NODESET} -i ${BASE_ONTOLOGY} core.ttl -v http://example.com/v0.1/DI/ -p devices -o devices.ttl
echo Prepare machinery
python3 ${DEBUG_CMDLINE} ../nodeset2owl.py ${MACHINERY_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl -v http://example.com/v0.1/Machinery/ -p machinery -o machinery.ttl
echo Test pumps
python3 ${DEBUG_CMDLINE} ../nodeset2owl.py  ${PUMPS_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl -v http://example.com/v0.1/Pumps/ -p pumps -o ${RESULT}
python3 $CLEANGRAPH $RESULT $CLEANED
diff $CLEANED $comparewith
rm -f core.ttl device.ttl machinery.ttl

#rm -f ${CLEANED} ${RESULT}