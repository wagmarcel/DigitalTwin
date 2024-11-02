import asyncio
import argparse
from asyncua import Client
from asyncua import ua
import xml.etree.ElementTree as ET
import sys
from asyncua.ua import NodeIdType
import traceback
from asyncua.common.xmlexporter import XmlExporter

sys.setrecursionlimit(1500)  # Increase the recursion limit to avoid maximum recursion depth error

debug = False
async def browse_node(client, node, exported_nodes, visited_nodes, export_namespace_indexes, parent_node_id=None):
    """
    Browse the given node and add its information to the XML in a flat structure.
    """
    try:
        # Avoid re-visiting nodes to prevent infinite recursion
        if node.nodeid in visited_nodes:
            return
        visited_nodes.add(node.nodeid)
        print(f"visited: {node.nodeid.NamespaceIndex}:{node.nodeid.Identifier}") if debug else False

        # If the node belongs to a relevant namespace, add it to the XML
        xml_node = None
        if node.nodeid.NamespaceIndex in export_namespace_indexes:
            exported_nodes.append(node)

        # Browse children nodes and add them to the XML root
        references = await node.get_references()
        for ref in references:
            # Always browse the child nodes, filter them later
            child_node = client.get_node(ref.NodeId)
            await browse_node(client, child_node, exported_nodes, visited_nodes, export_namespace_indexes, parent_node_id=node.nodeid)

    except Exception as e:
        print(f"Error browsing node: {e}")
        traceback.print_exc()

async def main():
    global debug
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Dump OPC UA server nodeset to XML.')
    parser.add_argument('--server-url', type=str, default='opc.tcp://localhost:4840/freeopcua/server/', help='OPC UA server URL (default is opc.tcp://localhost:4840/freeopcua/server/)')
    parser.add_argument('--start-node', type=str, default='i=84', help='Node ID to start browsing from (default is the Root node, i=84)')
    parser.add_argument('--output-file', type=str, default='nodeset2.xml', help='Output XML file name (default is nodeset2.xml)')
    parser.add_argument('--namespaces', type=str, nargs='*', help='List of Namespaces to collect nodes from.')
    parser.add_argument('-d','--debug', action="store_true", default=False, help="Set debug flag.")
    args = parser.parse_args()

    debug = args.debug
    # Connect to the OPC UA server
    async with Client(url=args.server_url) as client:
        # Create XML root for the NodeSet
        exporter = XmlExporter(client, export_values=True)

        # Get the namespace URIs from the server
        namespace_uris = await client.get_namespace_array()

        # Create NamespaceUris element
        #namespace_uris_element = ET.SubElement(xml_root, 'NamespaceUris')
        export_namespace_indexes = []

        if args.namespaces is None:
            print(f"Please provide a namespace, e.g. one of {namespace_uris}.")
            exit(1)
        for index, uri in enumerate(namespace_uris):
            # Only resolve requested namespaces
            if uri in args.namespaces:
                nsidx = await client.get_namespace_index(uri)
                export_namespace_indexes.append(nsidx)


        # Get the starting node
        exported_nodes = []
        start_node = client.get_node(args.start_node)

        # Start browsing from the specified start node
        visited_nodes = set()  # Track visited nodes to avoid infinite recursion
        await browse_node(client, start_node, exported_nodes, visited_nodes, export_namespace_indexes)

        # Generate the XML tree
        await exporter.build_etree(exported_nodes)

        # Write to the nodeset2.xml file with pretty formatting
        #from xml.dom import minidom
        #xml_str = ET.tostring(xml_root, encoding='utf-8')
        #pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ")
        #with open(args.output_file, "w", encoding='utf-8') as f:
        #    f.write(pretty_xml_str)
        await exporter.write_xml(args.output_file)

if __name__ == "__main__":
    asyncio.run(main())
