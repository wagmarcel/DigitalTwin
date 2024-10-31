import asyncio
import argparse
from asyncua import Client
import xml.etree.ElementTree as ET
import sys
from asyncua.ua import NodeIdType
import traceback

sys.setrecursionlimit(1500)  # Increase the recursion limit to avoid maximum recursion depth error

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
        if identifier_type == NodeIdType.Numeric:
            return f"ns={namespace_index};i={identifier}"
        elif identifier_type == NodeIdType.String:
            return f"ns={namespace_index};s={identifier}"
        elif identifier_type == NodeIdType.Guid:
            return f"ns={namespace_index};g={identifier}"
        elif identifier_type == NodeIdType.ByteString:
            return f"ns={namespace_index};b={identifier.hex()}" if isinstance(identifier, bytes) else f"ns={namespace_index};b={identifier}"
        elif identifier_type == NodeIdType.TwoByte:
            return f"ns={namespace_index};i={identifier}"  # Assuming TwoByte is treated similar to a Numeric identifier
        elif identifier_type == NodeIdType.FourByte:
            return f"ns={namespace_index};i={identifier}"  # Assuming FourByte is treated similar to a Numeric identifier
        else:
            raise ValueError(f"Unsupported NodeId type: {identifier_type}")
    except Exception as e:
        print(f"Error formatting NodeId: {e}")
        traceback.print_exc()
        raise

async def browse_node(client, node, xml_root, visited_nodes):
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

        browse_name = await node.read_browse_name()
        display_name = await node.read_display_name()
        node_class = await node.read_node_class()

        # Format BrowseName as "prefix:name"
        browse_name_str = f"{browse_name.NamespaceIndex}:{browse_name.Name}"

        # Create an XML element for the node in the flat structure
        xml_node = ET.SubElement(xml_root, f'UA{node_class.name}')
        xml_node.set('NodeId', str(node_id))
        xml_node.set('BrowseName', browse_name_str)
        

        # Add DisplayName as a sub-element
        display_name_element = ET.SubElement(xml_node, 'DisplayName')
        display_name_element.text = str(display_name.Text)

        # Add References as a sub-element
        references_element = ET.SubElement(xml_node, 'References')

        # Browse children nodes and add them to the XML root
        references = await node.get_references()
        for ref in references:
            reference_type = format_nodeid(ref.ReferenceTypeId)
            is_forward = ref.IsForward

            # Create a Reference element for each reference
            ref_element = ET.SubElement(references_element, 'Reference')
            ref_element.set('ReferenceType', reference_type)
            ref_element.set('IsForward', str(is_forward).lower())  # Set IsForward as a boolean string (true/false)
            ref_element.text = format_nodeid(ref.NodeId)

            if is_forward:
                child_node = client.get_node(ref.NodeId)
                await browse_node(client, child_node, xml_root, visited_nodes)

    except Exception as e:
        print(f"Error browsing node: {e}")
        traceback.print_exc()

async def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Dump OPC UA server nodeset to XML.')
    parser.add_argument('--server-url', type=str, default='opc.tcp://localhost:4840/freeopcua/server/', help='OPC UA server URL (default is opc.tcp://localhost:4840/freeopcua/server/)')
    parser.add_argument('--start-node', type=str, default='i=84', help='Node ID to start browsing from (default is the Root node, i=84)')
    parser.add_argument('--output-file', type=str, default='nodeset2.xml', help='Output XML file name (default is nodeset2.xml)')
    args = parser.parse_args()

    # Connect to the OPC UA server
    async with Client(url=args.server_url) as client:
        # Get the starting node
        start_node = client.get_node(args.start_node)

        # Create XML root for the NodeSet
        xml_root = ET.Element('UANodeSet')

        # Start browsing from the specified start node
        visited_nodes = set()  # Track visited nodes to avoid infinite recursion
        await browse_node(client, start_node, xml_root, visited_nodes)

        # Generate the XML tree
        tree = ET.ElementTree(xml_root)

        # Write to the nodeset2.xml file with pretty formatting
        from xml.dom import minidom
        xml_str = ET.tostring(xml_root, encoding='utf-8')
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ", encoding='utf-8').decode('utf-8')
        with open(args.output_file, "w", encoding='utf-8') as f:
            f.write(pretty_xml_str)

if __name__ == "__main__":
    asyncio.run(main())
