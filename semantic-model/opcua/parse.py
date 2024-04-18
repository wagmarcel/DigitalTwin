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
    'http://opcfoundation.org/UA/': 'opcua',
    'http://opcfoundation.org/UA/Pumps/': 'pumps',
    'http://opcfoundation.org/UA/Machinery/': 'machinery',
    'http://opcfoundation.org/UA/DI/': 'devices'
}
unknown_ns_prefix = "ns"
versionIRI = URIRef("http://example.com/v0.1/UA/")
ontology_name = URIRef("http://opcfoundation.org/UA/Pumps/")
imported_ontologies = [URIRef('http://opcfoundation.org/UA/')]
aliases = [{
    22: 'opcua:Structure',
    29: 'opcua:Enumeration',
    884: 'opcua:Range',
    12755: 'opcua:OptionSet'
}]


uagraph = Graph()
uagraph.parse('base.ttl')
known_ns_classes = {}
for s, p, o in uagraph.triples((None, rdf_ns['opcua']['hasUri'], None)):
    print(s, p, o)
    known_ns_classes[o.toPython()] = s
    
def create_header(g):
    g.add((ontology_name, RDF.type, OWL.Ontology))
    g.add((ontology_name, OWL.versionIRI, versionIRI))
    g.add((ontology_name, OWL.versionInfo, Literal(0.1)))
    for ontology in imported_ontologies:
        g.add((ontology_name, OWL.imports, ontology))
    #g.add((rdf_ns['pumps']['PumpsNamespace'], RDF.type, rdf_ns['opcua']['Namespace']))
    #g.add((rdf_ns['pumps']['PumpsNamespace'], rdf_ns['opcua']['hasUri'], Literal(ontology_name.toPython())))


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
        aliases.append({})
        rdf_ns[prefix] = namespace
        g.bind(prefix, namespace)
        print(f'Added RDF namespace {namespace} with prefix {prefix}')


def split_ns_term(nsterm):
    parts = nsterm.split(':', 1)
    if len(parts) == 2:
        ns_index, name = parts
        return int(ns_index), name
    else:
        return None, nsterm


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


def get_reference_subtype(node):
    subtype = None
    references = node.find('opcua:References', xml_ns)
    refs = references.findall('opcua:Reference', xml_ns)
    for ref in refs:
        reftype = ref.get('ReferenceType')
        isForward = ref.get('IsForward')
        #print(reftype, isForward)
        if reftype == 'HasSubtype' and isForward == 'false':
            nsid, id = parse_nodeid(ref.text)
            try:
                subtype = aliases[nsid][id]
            except:
                print(f"Warning: Could not find type ns={nsid};i={id}")
                subtype = None
    return subtype
            

#def add_nodeid_to_class(g, classiri, nodeid, namespaceid=0):
#    g.add((classiri, rdf_ns['opcua']['hasNodeId'], Literal(nodeid)))
#    namespace = opcua_ns[namespaceid]
#    g.add((classiri, rdf_ns['opcua']['hasNamespace'], known_ns_classes[namespace]))
def add_nodeid_to_class(g, node, nodeclasstype):
    nodeid = node.get('NodeId')
    ni_index, ni_id = parse_nodeid(nodeid)
    browsename = node.get('BrowseName')
    bn_index, bn_name = split_ns_term(browsename)
    index = ni_index
    if bn_index is not None:
        index = bn_index
    rdf_namespace = get_rdf_ns_from_ua_index(index)
    classiri = rdf_namespace[bn_name]
    g.add((classiri, rdf_ns['opcua']['hasNodeId'], Literal(ni_id)))
    namespace = opcua_ns[index]
    g.add((classiri, rdf_ns['opcua']['hasNamespace'], known_ns_classes[namespace]))
    g.add((classiri, RDF.type, rdf_ns['opcua'][nodeclasstype]))
    return get_rdf_ns_from_ua_index(index), bn_name
    #add_nodeid_to_class(g, classiri, ni_id, index)
                        

def parse_nodeid(nodeid):
    """
    Parses a NodeId in the format 'ns=X;i=Y' and returns a dictionary with the namespace index and identifier.
    
    Args:
    nodeid (str): The NodeId to parse.

    Returns:
    tuple for ns, i
    """
    ns_index = 0
    try:
        ns_part, i_part = nodeid.split(';')
    except:
        ns_part = None
        i_part = nodeid
    if ns_part is not None:
        ns_index = int(ns_part.split('=')[1])
    identifier = int(i_part.split('=')[1])
    return ns_index, identifier



def add_uavariable(g, uavariable):
    add_nodeid_to_class(g, uavariable, 'VariableNodeClass')
    # nodeid = uavariable.get('NodeId')
    # ni_index, ni_id = parse_nodeid(nodeid)
    # browsename = uavariable.get('BrowseName')
    # bn_index, bn_name = split_ns_term(browsename)
    # index = ni_index
    # if bn_index is not None:
    #     index = bn_index
    # rdf_namespace = get_rdf_ns_from_ua_index(index)
    # classname = rdf_namespace[bn_name]

    # add_nodeid_to_class(g, classname, ni_id, index)
    #g.add((classname, RDF.type, rdf_ns['opcua']['VariableNodeClass']))


def add_uadatatype(g, uadatatype):
    rdf_namespace, name = add_nodeid_to_class(g, uadatatype, 'DataTypeNodeClass')
    # browse_name = uadatatype.get('BrowseName')
    # nodeid = uadatatype.get('NodeId')
    # ni_index, ni_id = parse_nodeid(nodeid)
    # bn_index, name = split_ns_term(browse_name)
    # index = ni_index
    # if bn_index is not None:
    #     index = bn_index
    # rdf_namespace = get_rdf_ns_from_ua_index(index)
    
    # classname = rdf_namespace[name]
    # #g.add((rdf_namespace[name], RDF.type, OWL.Class))
    # add_nodeid_to_class(g, classname, ni_id, index)
    subtype = get_reference_subtype(uadatatype)
    
    #g.add((rdf_namespace[name], rdf_ns['opcua']['hasNodeId'], Literal(nodeid)))
    if subtype is not None:
        g.add((rdf_namespace[name], RDFS.subClassOf, g.namespace_manager.expand_curie(subtype)))
    definition = uadatatype.find('opcua:Definition', xml_ns)
    fields = definition.findall('opcua:Field', xml_ns)
    for field in fields:
        elementname = field.get('Name')
        symbolicname = field.get('SymbolicName')
        if symbolicname is None:
            symbolicname = elementname
        value = field.get('Value')
        g.add((rdf_namespace[symbolicname], RDF.type, rdf_namespace[name]))
        g.add((rdf_namespace[symbolicname], rdf_ns['opcua']['hasValue'], Literal(str(value))))


tree = ET.parse('/home/marcel/src/UA-Nodeset/Pumps/Opc.Ua.Pumps.NodeSet2.xml')
#calling the root element
root = tree.getroot()
#print("Root is",root)
namespace_uris = root.find('opcua:NamespaceUris', xml_ns)
g = Graph()

create_prefixes(g, namespace_uris)
create_header(g)
uadatatypes = root.findall('opcua:UADataType', xml_ns)
for uadatatype in uadatatypes:
    add_uadatatype(g, uadatatype)

uavariables = root.findall('opcua:UAVariable', xml_ns)
for uavariable in uavariables:
    add_uavariable(g, uavariable)

write_graph(g, "result.ttl")