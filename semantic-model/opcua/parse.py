import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS


xml_ns = {
    'opcua': 'http://opcfoundation.org/UA/2011/03/UANodeSet.xsd'
}
rdf_ns = {
    'opcua': Namespace('http://opcfoundation.org/UA/')
}
opcua_ns = ['http://opcfoundation.org/UA/']
known_opcua_ns = {
    'http://opcfoundation.org/UA/Pumps/': 'pumps',
    'http://opcfoundation.org/UA/Machinery/': 'machinery',
    'http://opcfoundation.org/UA/DI/': 'devices'
}
unknown_ns_prefix = "ns"
versionIRI = URIRef("http://example.com/v0.1/UA/")
ontology_name = URIRef("http://opcfoundation.org/UA/Pumps/")
imported_ontologies = [URIRef('http://opcfoundation.org/UA/')]

def create_header(g):
    g.add((ontology_name, RDF.type, OWL.Ontology))
    g.add((ontology_name, OWL.versionIRI, versionIRI))
    g.add((ontology_name, OWL.versionInfo, Literal(0.1)))
    for ontology in imported_ontologies:
        g.add((ontology_name, OWL.imports, ontology))

def create_prefixes(g, xml_node):
    unknown_ns_count = 0
    opcua_ns_count = 1
    g.bind('opcua', rdf_ns['opcua'])
    for ns in xml_node:
        namespace = Namespace(ns.text)
        try:
            prefix = known_opcua_ns[ns.text]
        except:            
            prefix = f'{unknown_ns_prefix}{unknown_ns_count}'
            unknown_ns_count+=1
            known_opcua_ns[ns.text] = prefix
        opcua_ns.append(ns.text)
        rdf_ns[prefix] = namespace
        g.bind(prefix, namespace)
        print(f'Added RDF namespace {namespace} with prefix {prefix}')


def split_ns_term(nsterm):
    parts = nsterm.split(':', 1)
    if len(parts) == 2:
        ns_index, name = parts
        return int(ns_index), name
    else:
        raise ValueError(f'Invalid BrowseName format {nsterm}')


def get_rdf_ns_from_ua_index(index):
    namespace_uri = opcua_ns[int(index)]
    prefix = known_opcua_ns[namespace_uri]
    namespace = rdf_ns[prefix]
    return namespace


def dump_graph(g):
    for s, p, o in g:
        print(s, p, o)


def write_graph(g, filename):
    g.serialize(destination=filename)


def add_uadatatype(g, uadatatype):
    browse_name = uadatatype.get('BrowseName')
    nodeid = uadatatype.get('NodeId')
    ns_index, name = split_ns_term(browse_name)
    rdf_namespace = get_rdf_ns_from_ua_index(ns_index)
    classname = rdf_namespace[name]
    #g.add((rdf_namespace[name], RDF.type, OWL.Class))
    g.add((rdf_namespace[name], rdf_ns['opcua']['NodeId'], Literal(nodeid)))
    g.add((rdf_namespace[name], RDFS.subClassOf, rdf_ns['opcua']['Enumeration']))
    definition = uadatatype.find('opcua:Definition', xml_ns)
    fields = definition.findall('opcua:Field', xml_ns)
    for field in fields:
        elementname = field.get('Name')
        symbolicname = field.get('SymbolicName')
        if symbolicname is None:
            symbolicname = elementname
        value = field.get('Value')
        g.add((rdf_namespace[symbolicname], RDF.type, classname))
        g.add((rdf_namespace[symbolicname], rdf_ns['opcua']['hasValue'], Literal(str(value))))


tree = ET.parse('/home/marcel/src/UA-Nodeset/Pumps/Opc.Ua.Pumps.NodeSet2.xml')
#calling the root element
root = tree.getroot()
print("Root is",root)
namespace_uris = root.find('opcua:NamespaceUris', xml_ns)
g = Graph()
create_header(g)
create_prefixes(g, namespace_uris)

uadatatypes = root.findall('opcua:UADataType', xml_ns)
for uadatatype in uadatatypes:
    add_uadatatype(g, uadatatype)

write_graph(g, "result.ttl")