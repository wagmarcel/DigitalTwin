
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

echo create core.ttl
python3 nodeset2owl.py ${CORE_NODESET} -i ${BASE_ONTOLOGY} -v http://example.com/v0.1/UA/ -p opcua -o core.ttl
echo create devices.ttl
python3 nodeset2owl.py  ${DI_NODESET} -i ${BASE_ONTOLOGY} core.ttl -v http://example.com/v0.1/DI/ -p devices -o devices.ttl
echo create ia.ttl \(industrial automation\)
python3 nodeset2owl.py  ${IA_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl -v http://example.com/v0.1/IA/ -p ia -o ia.ttl
echo create machinery.ttl
python3 nodeset2owl.py ${MACHINERY_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl -v http://example.com/v0.1/Machinery/ -p machinery -o machinery.ttl
echo create pumps.ttl
python3 nodeset2owl.py  ${PUMPS_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl -v http://example.com/v0.1/Pumps/ -p pumps -o pumps.ttl
echo create pumpexample.ttl
python3 nodeset2owl.py  ${PUMP_EXAMPLE_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl pumps.ttl -n http://yourorganisation.org/InstanceExample/ -v http://example.com/v0.1/pumpexample/ -p pumpexample -o pumpexample.ttl
echo create machinetool.ttl
python3 nodeset2owl.py  ${MACHINETOOL_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl ia.ttl -v http://example.com/v0.1/MachineTool/ -p machinetool -o machinetool.ttl
echo create lasersystems.ttl
python3 nodeset2owl.py  ${LASERSYSTEMS_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl ia.ttl machinetool.ttl -v http://example.com/v0.1/LaserSystems/ -p lasersystems -o lasersystems.ttl
echo create lasersystemsexample.ttl
python3 nodeset2owl.py  ${LASERSYSTEMS_EXAMPLE_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl ia.ttl machinetool.ttl lasersystems.ttl -v http://example.com/v0.1/LaserSystems/ -p lasersystemsexample -o lasersystemsexample.ttl
echo create machinetoolexample.ttl
python3 nodeset2owl.py  ${MACHINETOOL_EXAMPLE_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl machinetool.ttl ia.ttl -n http://yourorganisation.org/MachineTool-Example/ -v http://example.com/MachineToolExample/v0.1/pumpexample/ -p machinetoolexample -o machinetoolexample.ttl
echo create machineryexample.ttl
python3 nodeset2owl.py  ${MACHINERY_EXAMPLE_NODESET} -i ${BASE_ONTOLOGY} core.ttl devices.ttl machinery.ttl -v http://example.com/MachineryExample/v0.1/pumpexample/ -p machineryexample -o machineryexample.ttl
echo create dictionary_irdi.ttl
python3 nodeset2owl.py  ${DICTIONARY_IRDI} -i ${BASE_ONTOLOGY} core.ttl -v http://example.com/v0.1/Dictionary/IRDI -p dictionary_irdi -o dictionary_irdi.ttl
echo create padim.ttl
python3 nodeset2owl.py  ${PADIM_NODESET} -i ${BASE_ONTOLOGY} core.ttl dictionary_irdi.ttl devices.ttl -v http://example.com/v0.1/PADIM -p padim -o padim.ttl
echo create machinery_processvalues.ttl
python3 nodeset2owl.py  ${MACHINERY_PROCESSVALUES_NODESET} -i ${BASE_ONTOLOGY} core.ttl padim.ttl -v http://example.com/v0.1/Machinery/ProcessValues -p machinery_processvalues -o machinery_processvalues.ttl
echo create machinery_jobs.ttl
python3 nodeset2owl.py  ${MACHINERY_JOBS_NODESET} -i ${BASE_ONTOLOGY} core.ttl  -v http://example.com/v0.1/Machinery/Jobs -p machinery_jobs -o machinery_jobs.ttl