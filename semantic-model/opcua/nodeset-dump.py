import asyncio
import argparse
from asyncua import Client
import xml.etree.ElementTree as ET
import sys
from asyncua.ua import NodeIdType
import traceback

sys.setrecursionlimit(1500)  # Increase the recursion limit to avoid maximum recursion depth error

# Define aliases dictionary for commonly used NodeIds
ALIASES = {
    "Boolean": "i=1",
    "SByte": "i=2",
    "Byte": "i=3",
    "Int16": "i=4",
    "UInt16": "i=5",
    "Int32": "i=6",
    "UInt32": "i=7",
    "Int64": "i=8",
    "UInt64": "i=9",
    "Float": "i=10",
    "Double": "i=11",
    "String": "i=12",
    "DateTime": "i=13",
    "Guid": "i=14",
    "ByteString": "i=15",
    "XmlElement": "i=16",
    "NodeId": "i=17",
    "ExpandedNodeId": "i=18",
    "StatusCode": "i=19",
    "QualifiedName": "i=20",
    "LocalizedText": "i=21",
    "Structure": "i=22",
    "DataValue": "i=23",
    "BaseDataType": "i=24",
    "DiagnosticInfo": "i=25",
    "Number": "i=26",
    "Integer": "i=27",
    "UInteger": "i=28",
    "Enumeration": "i=29",
    "HasComponent": "i=47",
    "Organizes": "i=35",
    "HasModellingRule": "i=37",
    "HasEncoding": "i=38",
    "HasDescription": "i=39",
    "HasTypeDefinition": "i=40",
    "GeneratesEvent": "i=41",
    "HasSubtype": "i=45",
    "HasProperty": "i=46",
    "IdType": "i=256",
    "NumericRange": "i=291",
    "Argument": "i=296",
    "Range": "i=884",
    "EUInformation": "i=887",
    "EnumValueType": "i=7594",
    "HasInterface": "i=17603"
}

def format_nodeid(nodeid):
    """
    Format the NodeId depending on its type.
    """
    namespace_index = nodeid.NamespaceIndex
    identifier = nodeid.Identifier
    identifier_type = nodeid.NodeIdType  # Corrected to use NodeIdType property

    if identifier is None:
        raise ValueError("NodeId has an undefined identifier, which is not supported.")

    try:
        if identifier_type == NodeIdType.Numeric or identifier_type == NodeIdType.TwoByte or identifier_type == NodeIdType.FourByte:
            # Check if the identifier has an alias, including explicit ns=0
            if namespace_index == 0:
                alias = next((key for key, value in ALIASES.items() if value in [f"i={identifier}", f"ns=0;i={identifier}"]), None)
                if alias:
                    return alias
            return f"ns={namespace_index};i={identifier}"
        elif identifier_type == NodeIdType.String:
            return f"ns={namespace_index};s={identifier}"
        elif identifier_type == NodeIdType.Guid:
            return f"ns={namespace_index};g={identifier}"
        elif identifier_type == NodeIdType.ByteString:
            return f"ns={namespace_index};b={identifier.hex()}" if isinstance(identifier, bytes) else f"ns={namespace_index};b={identifier}"
        else:
            raise ValueError(f"Unsupported NodeId type: {identifier_type}")
    except Exception as e:
        print(f"Error formatting NodeId: {e}")
        traceback.print_exc()
        raise

async def browse_node(client, node, xml_root, visited_nodes, export_namespace_indexes, parent_node_id=None):
    """
    Browse the given node and add its information to the XML in a flat structure.
    """
    try:
        # Avoid re-visiting nodes to prevent infinite recursion
        if node.nodeid in visited_nodes:
            return
        visited_nodes.add(node.nodeid)
        print(f"visited: {node.nodeid.NamespaceIndex}:{node.nodeid.Identifier}")

        # Format NodeId using the helper function
        node_id = format_nodeid(node.nodeid)

        # Always browse children, but only add nodes with relevant namespaces to XML
        browse_name = await node.read_browse_name()
        display_name = await node.read_display_name()
        node_class = await node.read_node_class()

        # If the node belongs to a relevant namespace, add it to the XML
        xml_node = None
        if node.nodeid.NamespaceIndex in export_namespace_indexes:
            # Format BrowseName as "prefix:name"
            if parent_node_id is not None:
                        parent_node_id_str = format_nodeid(parent_node_id)
            else:
                        parent_node_id_str = ''
            browse_name_str = f"{browse_name.NamespaceIndex}:{browse_name.Name}"

            # Create an XML element for the node in the flat structure
            xml_node = ET.SubElement(xml_root, f'UA{node_class.name}')
            xml_node.set('NodeId', str(node_id))
            xml_node.set('BrowseName', browse_name_str)
            if parent_node_id_str:
                        xml_node.set('ParentNodeId', parent_node_id_str)

            # Add DisplayName as a sub-element
            display_name_element = ET.SubElement(xml_node, 'DisplayName')
            display_name_element.text = str(display_name.Text)

            # Add References as a sub-element
            references_element = ET.SubElement(xml_node, 'References')
        else:
            references_element = None

        # Browse children nodes and add them to the XML root
        references = await node.get_references()
        for ref in references:
            reference_type = format_nodeid(ref.ReferenceTypeId)
            is_forward = ref.IsForward

            # Always browse the child nodes
            child_node = client.get_node(ref.NodeId)
            await browse_node(client, child_node, xml_root, visited_nodes, export_namespace_indexes, parent_node_id=node.nodeid)

            # If the reference points to a relevant namespace, add the reference to the XML
            if ref.NodeId.NamespaceIndex in export_namespace_indexes and xml_node is not None:
                ref_element = ET.SubElement(references_element, 'Reference')
                ref_element.set('ReferenceType', reference_type)
                ref_element.set('IsForward', str(is_forward).lower())  # Set IsForward as a boolean string (true/false)
                ref_element.text = format_nodeid(ref.NodeId)

    except Exception as e:
        print(f"Error browsing node: {e}")
        traceback.print_exc()

async def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Dump OPC UA server nodeset to XML.')
    parser.add_argument('--server-url', type=str, default='opc.tcp://localhost:4840/freeopcua/server/', help='OPC UA server URL (default is opc.tcp://localhost:4840/freeopcua/server/')
    parser.add_argument('--start-node', type=str, default='i=84', help='Node ID to start browsing from (default is the Root node, i=84)')
    parser.add_argument('--output-file', type=str, default='nodeset2.xml', help='Output XML file name (default is nodeset2.xml)')
    parser.add_argument('--ignore-namespaces', type=str, nargs='*', default=['http://opcfoundation.org/UA/'], help='List of additional namespaces to ignore (default is OPC UA standard namespaces)')
    args = parser.parse_args()

    # Connect to the OPC UA server
    async with Client(url=args.server_url) as client:
        # Create XML root for the NodeSet
        xml_root = ET.Element('UANodeSet')

        # Get the namespace URIs from the server
        namespace_uris = await client.get_namespace_array()

        # Create NamespaceUris element
        namespace_uris_element = ET.SubElement(xml_root, 'NamespaceUris')
        export_namespace_indexes = []

        for index, uri in enumerate(namespace_uris):
            # Add all namespaces, whether they are ignored or not
            uri_element = ET.SubElement(namespace_uris_element, 'Uri')
            uri_element.text = uri
            # Only add to exportable namespaces if not ignored
            if uri not in args.ignore_namespaces:
                export_namespace_indexes.append(index)

        # Create Aliases element
        aliases_element = ET.SubElement(xml_root, 'Aliases')
        for alias, node_id in ALIASES.items():
            alias_element = ET.SubElement(aliases_element, 'Alias')
            alias_element.set('Alias', alias)
            alias_element.text = node_id

        # Get the starting node
        start_node = client.get_node(args.start_node)

        # Start browsing from the specified start node
        visited_nodes = set()  # Track visited nodes to avoid infinite recursion
        await browse_node(client, start_node, xml_root, visited_nodes, export_namespace_indexes, parent_node_id=None)

        # Generate the XML tree
        tree = ET.ElementTree(xml_root)

        # Write to the nodeset2.xml file with pretty formatting
        from xml.dom import minidom
        xml_str = ET.tostring(xml_root, encoding='utf-8')
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ")
        with open(args.output_file, "w", encoding='utf-8') as f:
            # Write the corrected XML header with encoding and the pretty XML content
            #f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            for line in pretty_xml_str.splitlines():
                if line.strip():  # Avoid writing empty lines from prettify
                    f.write(line + "\n")

if __name__ == "__main__":
    asyncio.run(main())
