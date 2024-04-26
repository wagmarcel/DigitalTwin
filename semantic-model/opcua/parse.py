import sys
import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS
import argparse

query_namespaces = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX opcua: <http://opcfoundation.org/UA/>
SELECT ?uri ?prefix ?ns WHERE {
    ?ns rdf:type opcua:Namespace .
    ?ns opcua:hasUri ?uri .
    ?ns opcua:hasPrefix ?prefix .
}
"""
def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset and create RDF-graph <nodeset2.xml>')

    parser.add_argument('nodeset2', help='Path to the nodeset2 file')
    parser.add_argument('-i','--inputs', nargs='*', help='<Required> add dependent nodesets')
    parser.add_argument('-o', '--output', help='Resulting file.', default="result.ttl")
    parser.add_argument('-n', '--namespace', help='Namespace of ouput ontology, e.g. http://opcfoundation.org/UA/Pumps/',  required=True)
    parser.add_argument('-v', '--versionIRI', help='VersionIRI of ouput ontology, e.g. http://example.com/v0.1/UA/ ',  required=True)
    parser.add_argument('-p', '--prefix', help='Prefix for added ontolgoy, e.g. "pumps"',  required=True)
    parsed_args = parser.parse_args(args)
    return parsed_args

xml_ns = {
    'opcua': 'http://opcfoundation.org/UA/2011/03/UANodeSet.xsd'
}
rdf_ns = {
    'opcua': Namespace('http://opcfoundation.org/UA/')
}
opcua_ns = ['http://opcfoundation.org/UA/']
known_opcua_ns = {
     'http://opcfoundation.org/UA/': 'opcua'
 }
#     'http://opcfoundation.org/UA/Pumps/': 'pumps',
#     'http://opcfoundation.org/UA/Machinery/': 'machinery',
#     'http://opcfoundation.org/UA/DI/': 'devices'
# }
#known_opcua_ns = {}
known_ns_classes = {
    'http://opcfoundation.org/UA/': URIRef('http://opcfoundation.org/UA/OPCUANamespace')}
unknown_ns_prefix = "ns"
versionIRI = None #= URIRef("http://example.com/v0.1/UA/")
ontology_name = None #= URIRef("http://opcfoundation.org/UA/Pumps/")
imported_ontologies = [URIRef('http://opcfoundation.org/UA/')]
aliases = {}
nodeIds = [{}]
typeIds = [{}]
ig = Graph() # graph from inputs
g = Graph() # graph wich is currently created

def init_nodeids(base_ontologies, ontology_name, ontology_prefix):
    #uagraph = Graph()
    global ig
    for file in base_ontologies:
        hgraph = Graph()
        hgraph.parse(file)
        ig += hgraph
    query_result = ig.query(query_namespaces)
    for uri, prefix, ns in query_result:
        print(f"found {prefix}: {uri}  with namespaceclass {ns}")
        known_opcua_ns[str(uri)] = str(prefix)
        nodeIds.append({})
        
    rdf_ns[ontology_prefix] = Namespace(str(ontology_name))
    namespaceclass = f"OPCUA{ontology_prefix.upper()}Namespace"
          
    known_ns_classes[str(ontology_name)] = rdf_ns[ontology_prefix][namespaceclass]
    known_opcua_ns[ontology_name.toPython()] = ontology_prefix
    nodeIds.append({})
    g.add((rdf_ns[ontology_prefix][namespaceclass], RDF.type, rdf_ns['opcua']['Namespace']))
    g.add((rdf_ns[ontology_prefix][namespaceclass], rdf_ns['opcua']['hasUri'], Literal(ontology_name.toPython())))
    g.add((rdf_ns[ontology_prefix][namespaceclass], rdf_ns['opcua']['hasPrefix'], Literal(ontology_prefix)))
    # for s, p, o in uagraph.triples((None, RDF.type, rdf_ns['opcua']['Namespace'])):
    #     print(s, p, o)
    #     for s, p, o in uagraph.triples((None, rdf_ns['opcua']['hasUri'], None)):
    #         known_ns_classes
    #     known_ns_classes[o.toPython()] = s
    # for s, p, o in uagraph.triples((None, rdf_ns['opcua']['hasNodeId'], None)):
    #     nodeIds[0][int(o)] = s
    # nodeIds.append({})
    # nodeIds.append({})
    # nodeIds.append({})

    
def create_header(g):
    g.add((ontology_name, RDF.type, OWL.Ontology))
    g.add((ontology_name, OWL.versionIRI, versionIRI))
    g.add((ontology_name, OWL.versionInfo, Literal(0.1)))
    for ontology in imported_ontologies:
        g.add((ontology_name, OWL.imports, ontology))
    #g.add((rdf_ns['pumps']['PumpsNamespace'], RDF.type, rdf_ns['opcua']['Namespace']))
    #g.add((rdf_ns['pumps']['PumpsNamespace'], rdf_ns['opcua']['hasUri'], Literal(ontology_name.toPython())))


def create_prefixes(g, xml_node):
    if xml_node is None:
        return
    unknown_ns_count = 0
    opcua_ns_count = 10
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
        #nodeIds.append({})
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
                subtype = nodeIds[nsid][id]
            except:
                print(f"Warning: Could not find type ns={nsid};i={id}")
                subtype = None
    return subtype
            
            
def add_datatype(g, node, classiri):
    datatype = node.get('DataType')
    if 'i=' not in datatype: # alias is used
        datatype = aliases[datatype]
    index, id = parse_nodeid(datatype)
    try:
        typeiri = nodeIds[index][id]
    except:
        print(f'Warning: Cannot find nodeId ns={index};i={id}')
        return
    if datatype is not None:
        g.add((classiri, rdf_ns['opcua']['hasDataType'], typeiri))


def add_subclass(g, node, classiri):
    subtype = get_reference_subtype(node)
    if subtype is not None:
        g.add((classiri, RDFS.subClassOf, subtype))


def add_to_nodeids(rdf_namespace, name, node):
    nodeid = node.get('NodeId')
    ni_index, ni_id = parse_nodeid(nodeid)
    prefix = known_opcua_ns[str(rdf_namespace)]
    nodeIds[ni_index][ni_id] = rdf_namespace[name]


def nodeId_to_iri(namespace, nid):
    return namespace[f'nodeId{nid}']

def add_nodeid_to_class(g, node, nodeclasstype, xml_ns):
    nid, index, bn_name = get_nid_ns_and_name(g, node)
    rdf_namespace = get_rdf_ns_from_ua_index(index)
    classiri = nodeId_to_iri(rdf_namespace, nid)
    g.add((classiri, rdf_ns['opcua']['hasNodeId'], Literal(nid)))
    g.add((classiri, rdf_ns['opcua']['hasBrowseName'], Literal(bn_name)))
    namespace = opcua_ns[index]
    g.add((classiri, rdf_ns['opcua']['hasNamespace'], known_ns_classes[namespace]))
    g.add((classiri, RDF.type, rdf_ns['opcua'][nodeclasstype]))
    nodeIds[index][nid] = classiri
    displayname_node = node.find('opcua:DisplayName', xml_ns)
    g.add((classiri, rdf_ns['opcua']['hasDisplayName'], Literal(displayname_node.text)))
    return rdf_namespace, classiri
                        

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


def add_uaobjecttype(g, node):
    rdf_namespace, name = add_nodeid_to_class(g, node, 'ObjectTypeNodeClass')
    add_subclass(g, node, rdf_namespace[name])
    add_to_nodeids(rdf_namespace, name, node)


def add_uavariable(g, uavariable):
    rdf_namespace, name = add_nodeid_to_class(g, uavariable, 'VariableNodeClass')
    add_datatype(g, uavariable, rdf_namespace[name])


def downcase_string(s):
    return s[0].lower() + s[1:]


def add_uadatatype(g, node, xml_ns):
    nid, index, name = get_nid_ns_and_name(g, node)
    rdf_namespace = get_rdf_ns_from_ua_index(index)
    classiri = nodeId_to_iri(rdf_namespace, nid)
    datatypeIri = rdf_namespace[name]
    #add_subclass(g, node, datatypeIri)
    definition = uadatatype.find('opcua:Definition', xml_ns)
    fields = definition.findall('opcua:Field', xml_ns)
    for field in fields:
        elementname = field.get('Name')
        symbolicname = field.get('SymbolicName')
        if symbolicname is None:
            symbolicname = elementname
        value = field.get('Value')
        g.add((rdf_namespace[symbolicname], RDF.type, rdf_ns['opcua']['Field']))
        g.add((rdf_namespace[symbolicname], rdf_ns['opcua']['hasValue'], Literal(str(value))))
        g.add((rdf_namespace[symbolicname], rdf_ns['opcua']['hasField'], rdf_namespace[symbolicname]))
        

def isNodeId(nodeId):
    return 'i=' in nodeId


def get_namespaced_browsename(index, id):
    # Is it part of current or input graph?
    namespace = get_rdf_ns_from_ua_index(index)
    graph = None
    if str(namespace) == ontology_name:
        graph = g
    else:
        graph = ig
    subject = graph.subjects((RDF.type, rdf_ns['opcua']['hasNodeId'], id))[0]
    browsename = graph.object((subject, rdf_ns['opcua']['hasBrowseName']))[0]
    return namespace()


def add_references_to_class(g, node, classiri, namespace, xml_ns):
    references_node = node.find('opcua:References', xml_ns)
    references = references_node.findall('opcua:Reference', xml_ns)
    for reference in references:
        reference_name = reference.get('ReferenceType')
        if not isNodeId(reference_name):
            referenceid = aliases[referenceid]
        ref_index, ref_id = parse_nodeid(referenceid)
        rdfnode = get_rdf_node(ref_index, ref_id)
        
        node_type = downcase_string(reference.get('ReferenceType'))
        nodeId = reference.text
        ni_index, ni_id = parse_nodeid(nodeId)
        target_namespace = get_rdf_ns_from_ua_index(ni_index)
        isForward = reference.get('IsForward')
        if isForward == 'false':
            print(node_type)
            g.add((nodeId_to_iri(target_namespace, ni_id), rdf_ns['opcua'][node_type], URIRef(classiri)))
        else:
            print(node_type)
            g.add((URIRef(classiri), rdf_ns['opcua'][node_type], nodeId_to_iri(target_namespace, ni_id)))


def add_uanode(g, node, type, xml_ns):
    namespace, classiri = add_nodeid_to_class(g, node, type, xml_ns)
    #add_references_to_class(g, node, classiri, namespace, xml_ns)

def resolve_alias(nodeid):
    alias = nodeid
    if not isNodeId(nodeid):
        alias = aliases[nodeid]
    return alias


def add_reference_type(g, node, xml_ns):
    browsename = node.get('BrowseName')
    nodeid = node.get('NodeId')
    ref_index, ref_id = parse_nodeid(nodeid)
    ref_namespace = get_rdf_ns_from_ua_index(ref_index)
    references_node = node.find('opcua:References', xml_ns)
    references = references_node.findall('opcua:Reference', xml_ns)
    if len(references) == 0:
        g.add((ref_namespace[browsename], RDF.type, OWL.Class))
    else:
        subtype = None
        for reference in references:
            reftype = reference.get('ReferenceType')
            nodeid = resolve_alias(reftype)
            reftype_index, reftype_id = parse_nodeid(nodeid)
            if reftype_id == 45 and reftype_index == 0:
                # HasSubtype detected
                subtype = reference.text    
                break
        nodeid = resolve_alias(subtype)
        subtype_index, subtype_id = parse_nodeid(subtype)
        typeiri = typeIds[subtype_index][subtype_id]
        g.add((ref_namespace[browsename], RDF.type, OWL.Class))
        g.add((ref_namespace[browsename], RDFS.subClassOf, typeiri))
    typeIds[ref_index][ref_id] = ref_namespace[browsename]
    return


def get_nid_ns_and_name(g, node):
    nodeid = node.get('NodeId')
    ni_index, ni_id = parse_nodeid(nodeid)
    browsename = node.get('BrowseName')
    bn_index, bn_name = split_ns_term(browsename)
    index = ni_index
    if bn_index is not None:
        index = bn_index
    #rdf_namespace = get_rdf_ns_from_ua_index(index)
    return ni_id, index, bn_name


def scan_aliases(alias_nodes):
    for alias in alias_nodes:
        name = alias.get('Alias')
        nodeid = alias.text
        aliases[name] = nodeid


if __name__ == '__main__':
    args = parse_args()
    upcua_nodeset = args.nodeset2
    opcua_inputs = args.inputs if args.inputs is not None else []
    opcua_output = args.output
    prefix = args.prefix
    versionIRI = URIRef(args.versionIRI)
    ontology_name = URIRef(args.namespace)
    ontology_prefix = args.prefix
    tree = ET.parse(upcua_nodeset)
    #calling the root element
    root = tree.getroot()

    #g = Graph()
    init_nodeids(opcua_inputs, ontology_name, ontology_prefix)
    namespace_uris = root.find('opcua:NamespaceUris', xml_ns)
    create_prefixes(g, namespace_uris)
    create_header(g)
    aliases_node = root.find('opcua:Aliases', xml_ns)
    alias_nodes = aliases_node.findall('opcua:Alias', xml_ns)
    scan_aliases(alias_nodes)
    tag_names = [('opcua:UADataType', 'DataTypeNodeClass'),
                 ('opcua:UAVariable', 'VariableNodeClass'), 
                 ('opcua:UAObjectType', 'ObjectTypeNodeClass'), 
                 ('opcua:UAOjbect', 'ObjectNodeClass'),
                 ('opcua:UAReferenceType', 'ReferenceTypeNodeClass'),
                 ('opcua:UAVariableType', 'VariableTypeNodeClass')]
    for tag_name, type in tag_names:
        uanodes = root.findall(tag_name, xml_ns)   
        for uanode in uanodes:
            add_uanode(g, uanode, type, xml_ns)
    uareferencetypes = root.findall('opcua:UAReferenceType', xml_ns)
    for uareferencetype in uareferencetypes:
        add_reference_type(g, uareferencetype, xml_ns)

    # uadatatypes = root.findall('opcua:UADataType', xml_ns)
    # for uadatatype in uadatatypes:
    #     add_uadatatype(g, uadatatype, xml_ns)

    # uavariables = root.findall('opcua:UAVariable', xml_ns)
    # for uavariable in uavariables:
    #     add_uavariable(g, uavariable)

    # uaobjecttypes = root.findall('opcua:UAObjectType', xml_ns)
    # for uaobjecttype in uaobjecttypes:
    #     add_uaobjecttype(g, uaobjecttype)
        
    write_graph(g, "result.ttl")