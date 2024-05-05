# Tools to translate from OPC/UA Information Model to Semantic Web standards

## nodeset2owl.py

For local testing

    export CORE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Schema/Opc.Ua.NodeSet2.xml
    export DI_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/DI/Opc.Ua.Di.NodeSet2.xml
    export MACHINERY_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Machinery/Opc.Ua.Machinery.NodeSet2.xml
    export PUMPS_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Pumps/Opc.Ua.Pumps.NodeSet2.xml
    export PUMP_EXAMPLE_NODESET=https://raw.githubusercontent.com/OPCFoundation/UA-Nodeset/UA-1.05.03-2023-12-15/Pumps/instanceexample.xml

Create core.ttl:

    python3 nodeset2owl.py ${CORE_NODESET} -i base.ttl  -n http://opcfoundation.org/UA/ -v http://example.com/v0.1/UA/ -p opcua -o core.ttl


Create devices.ttl:

    python3 nodeset2owl.py  ${DI_NODESET} -i base.ttl core.ttl  -n http://opcfoundation.org/UA/DI/ -v http://example.com/v0.1/DI/ -p devices -o devices.ttl


Create machinery.ttl:

    python3 nodeset2owl.py ${MACHINERY_NODESET} -i base.ttl core.ttl devices.ttl -n http://opcfoundation.org/UA/Machinery/ -v http://example.com/v0.1/Machinery/ -p machinery -o machinery.ttl


Create pumps.ttl:

    python3 nodeset2owl.py  ${PUMPS_NODESET} -i base.ttl core.ttl devices.ttl machinery.ttl -n http://opcfoundation.org/UA/Pumps/ -v http://example.com/v0.1/Pumps/ -p pumps -o pumps.ttl

create pumpexample.ttl:

    python3 nodeset2owl.py  ${PUMP_EXAMPLE_NODESET} -i base.ttl core.ttl devices.ttl machinery.ttl pumps.ttl -n http://yourorganisation.org/InstanceExample/ -v http://example.com/v0.1/pumpexample/ -p pumpexample -o pumpexample.ttl
