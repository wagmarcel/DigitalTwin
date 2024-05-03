import sys
import xml.etree.ElementTree as ET
import pathlib
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS
import argparse

query_namespaces = """
PREFIX op: <http://environment.data.gov.au/def/op#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX base: <http://opcfoundation.org/UA/Base/>
SELECT ?uri ?prefix ?ns WHERE {
    ?ns rdf:type base:Namespace .
    ?ns base:hasUri ?uri .
    ?ns base:hasPrefix ?prefix .
}
"""

query_nodeIds = """
PREFIX op: <http://environment.data.gov.au/def/op#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX base: <http://opcfoundation.org/UA/Base/>
PREFIX opcua: <http://opcfoundation.org/UA/>
SELECT ?nodeId ?uri ?node WHERE {
    ?node rdf:type/rdfs:subClassOf opcua:BaseNodeClass .
    ?node base:hasNodeId ?nodeId .
    ?node base:hasNamespace ?ns .
    ?ns base:hasUri ?uri .
}
"""

query_types = """
PREFIX op: <http://environment.data.gov.au/def/op#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX base: <http://opcfoundation.org/UA/Base/>
PREFIX opcua: <http://opcfoundation.org/UA/>
SELECT ?nodeId ?uri ?type WHERE {
  {?type rdfs:subClassOf* opcua:BaseDataType .
   ?node base:definesType ?type .
   ?node base:hasNodeId ?nodeId .
   ?node base:hasNamespace ?ns .
   ?ns base:hasUri ?uri .
  }
  UNION
  {?type rdfs:subClassOf* opcua:BaseObjectType .
   ?node base:definesType ?type .
   ?node base:hasNodeId ?nodeId .
   ?node base:hasNamespace ?ns .
   ?ns base:hasUri ?uri .
  }
   UNION
  {?type rdfs:subClassOf* opcua:BaseVariableType .
   ?node base:definesType ?type .
   ?node base:hasNodeId ?nodeId .
   ?node base:hasNamespace ?ns .
   ?ns base:hasUri ?uri .
  }
   UNION
  {?type rdfs:subClassOf* opcua:References .
   ?node base:definesType ?type .
   ?node base:hasNodeId ?nodeId .
   ?node base:hasNamespace ?ns .
   ?ns base:hasUri ?uri .
  }
}
"""

def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset and create RDF-graph <nodeset2.xml>')

    parser.add_argument('nodeset2', help='Path to the nodeset2 file')
    parser.add_argument('-i','--inputs', nargs='*', help='<Required> add dependent nodesets')
    parser.add_argument('-m','--imports', nargs='*', help='<Required> add imports')
    parser.add_argument('-o', '--output', help='Resulting file.', default="result.ttl")
    parser.add_argument('-n', '--namespace', help='Namespace of ouput ontology, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parser.add_argument('-v', '--versionIRI', help='VersionIRI of ouput ontology, e.g. http://example.com/v0.1/UA/ ',  required=True)
    parser.add_argument('-p', '--prefix', help='Prefix for added ontolgoy, e.g. "pumps"', required=True)
    parsed_args = parser.parse_args(args)
    return parsed_args

xml_ns = {
    'opcua': 'http://opcfoundation.org/UA/2011/03/UANodeSet.xsd'
}
# Namespaces defined for RDF usage
rdf_ns = {
    'opcua': Namespace('http://opcfoundation.org/UA/'),
    'base': Namespace('http://opcfoundation.org/UA/Base/')
}
# Contains the mapping from opcua-ns-index to ns
opcua_ns = ['http://opcfoundation.org/UA/']
# Contains the list of 
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
#imported_ontologies = [URIRef('http://opcfoundation.org/UA/Base')]
imported_ontologies = [URIRef('file:///home/marcel/src/IndustryFusion/DigitalTwin/semantic-model/opcua/base.ttl')]
aliases = {}
nodeIds = [{}]
typeIds = [{}]
ig = Graph() # graph from inputs
g = Graph() # graph wich is currently created

hasSubtypeId = 45
hasPropertyId = 46
hasTypeDefinition = 40
hasComponent = 47

def init_nodeids(base_ontologies, ontology_name, ontology_prefix):
    #uagraph = Graph()
    global ig
    for file in base_ontologies:
        hgraph = Graph()
        hgraph.parse(file)
        ig += hgraph
    query_result = ig.query(query_namespaces)
    corens = list(known_opcua_ns.keys())[0]
    for uri, prefix, ns in query_result:
        if str(uri) != corens:
            print(f"found {prefix}: {uri}  with namespaceclass {ns}")
            known_opcua_ns[str(uri)] = str(prefix)
            known_ns_classes[str(uri)] = ns
            rdf_ns[str(prefix)] = Namespace(str(uri))
            nodeIds.append({})
            typeIds.append({})    

    rdf_ns[ontology_prefix] = Namespace(str(ontology_name))
    namespaceclass = f"{ontology_prefix.upper()}Namespace"
    g.bind(ontology_prefix, Namespace(str(ontology_name)))
    
    known_ns_classes[str(ontology_name)] = rdf_ns[ontology_prefix][namespaceclass]
    known_opcua_ns[ontology_name.toPython()] = ontology_prefix
    nodeIds.append({})
    typeIds.append({})
    
    query_result = ig.query(query_nodeIds)
    #uris = known_opcua_ns.keys()
    uris = opcua_ns
    urimap = {}
    for idx, uri in enumerate(uris):
        urimap[uri] = idx
    for nodeId, uri, nodeIri in query_result:
        ns = urimap[str(uri)]
        #nId = f'ns={ns};i={nodeId}'
        nodeIds[ns][int(nodeId)] = nodeIri
    query_result = ig.query(query_types)
    for nodeId, uri, type in query_result:
        ns = urimap[str(uri)]
        typeIds[ns][int(nodeId)] = type

    g.add((rdf_ns[ontology_prefix][namespaceclass], RDF.type, rdf_ns['base']['Namespace']))
    g.add((rdf_ns[ontology_prefix][namespaceclass], rdf_ns['base']['hasUri'], Literal(ontology_name.toPython())))
    g.add((rdf_ns[ontology_prefix][namespaceclass], rdf_ns['base']['hasPrefix'], Literal(ontology_prefix)))

    
def create_header(g):
    g.add((ontology_name, RDF.type, OWL.Ontology))
    g.add((ontology_name, OWL.versionIRI, versionIRI))
    g.add((ontology_name, OWL.versionInfo, Literal(0.1)))
    for ontology in imported_ontologies:
        g.add((ontology_name, OWL.imports, ontology))


def create_prefixes(g, xml_node):
    g.bind('opcua', rdf_ns['opcua'])
    g.bind('base', rdf_ns['base'])
    if xml_node is None:
        return
    #unknown_ns_count = 0
    #opcua_ns_count = 10
    for ns in xml_node:
        #namespace = Namespace(ns.text)
        #try:
        #    prefix = known_opcua_ns[ns.text]
        #except:          
        #    prefix = f'{unknown_ns_prefix}{unknown_ns_count}'
        #    unknown_ns_count+=1
        #    known_opcua_ns[ns.text] = prefix
        opcua_ns.append(ns.text)
        #nodeIds.append({})
        #rdf_ns[prefix] = namespace
        #print(f'Added RDF namespace {namespace} with prefix {prefix}')


# def split_ns_term(nsterm):
#     parts = nsterm.split(':', 1)
#     if len(parts) == 2:
#         ns_index, name = parts
#         return int(ns_index), name
#     else:
#         return None, nsterm


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
        g.add((classiri, rdf_ns['base']['hasDataType'], typeiri))


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
    g.add((classiri, rdf_ns['base']['hasNodeId'], Literal(nid)))
    g.add((classiri, rdf_ns['base']['hasBrowseName'], Literal(bn_name)))
    namespace = opcua_ns[index]
    g.add((classiri, rdf_ns['base']['hasNamespace'], known_ns_classes[namespace]))
    g.add((classiri, RDF.type, rdf_ns['opcua'][nodeclasstype]))
    nodeIds[index][nid] = classiri
    displayname_node = node.find('opcua:DisplayName', xml_ns)
    g.add((classiri, rdf_ns['base']['hasDisplayName'], Literal(displayname_node.text)))
    symbolic_name = node.get('SymbolicName')
    if symbolic_name is not None:
        g.add((classiri, rdf_ns['base']['hasSymbolicName'], Literal(symbolic_name)))
    description_node = node.find('opcua:Description', xml_ns)
    if description_node is not None:
        description = description_node.text
        g.add((classiri, rdf_ns['base']['hasDescription'], Literal(description)))
    isSymmetric = node.get('Symmetric')
    if isSymmetric is not None:
        g.add((classiri, rdf_ns['base']['isSymmetric'], Literal(isSymmetric)))
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


# def add_uaobjecttype(g, node):
#     rdf_namespace, name = add_nodeid_to_class(g, node, 'ObjectTypeNodeClass')
#     add_subclass(g, node, rdf_namespace[name])
#     add_to_nodeids(rdf_namespace, name, node)


# def add_uavariable(g, uavariable):
#     rdf_namespace, name = add_nodeid_to_class(g, uavariable, 'VariableNodeClass')
#     add_datatype(g, uavariable, rdf_namespace[name])


def downcase_string(s):
    return s[0].lower() + s[1:]


def add_uadatatype(g, node, xml_ns):
    nid, index, name = get_nid_ns_and_name(g, node)
    rdf_namespace = get_rdf_ns_from_ua_index(index)
    classiri = nodeId_to_iri(rdf_namespace, nid)
    datatypeIri = rdf_namespace[name]
    #add_subclass(g, node, datatypeIri)
    definition = uadatatype.find('opcua:Definition', xml_ns)
    if definition is not None:
        fields = definition.findall('opcua:Field', xml_ns)
        for field in fields:
            elementname = field.get('Name')
            symbolicname = field.get('SymbolicName')
            if symbolicname is None:
                symbolicname = elementname
            value = field.get('Value')
            datatypeid = field.get('DataType')
            datatypeiri = None
            if datatypeid is not None:
                datatypeid = resolve_alias(datatypeid)
                datatype_index, datatype_id = parse_nodeid(datatypeid)
                datatypeiri = typeIds[datatype_index][datatype_id]
                g.add((rdf_namespace[symbolicname], rdf_ns['base']['hasDataType'], datatypeiri))
            g.add((rdf_namespace[symbolicname], RDF.type, rdf_ns['base']['Field']))
            if value is not None:
                g.add((rdf_namespace[symbolicname], rdf_ns['base']['hasValue'], Literal(str(value))))               
            g.add((rdf_namespace[symbolicname], rdf_ns['base']['hasFieldName'], Literal(str(symbolicname))))
            g.add((datatypeIri, rdf_ns['base']['hasField'], rdf_namespace[symbolicname]))
        

def isNodeId(nodeId):
    return 'i=' in nodeId


def getBrowsename(node):
    name = node.get('BrowseName')
    index = None
    if ':' in name:
        result = name.split(':', 1)
        name = result[1]
        index = int(result[0])
    return index, name

def get_namespaced_browsename(index, id):
    # Is it part of current or input graph?
    namespace = get_rdf_ns_from_ua_index(index)
    graph = None
    if str(namespace) == ontology_name:
        graph = g
    else:
        graph = ig
    subject = graph.subjects((RDF.type, rdf_ns['base']['hasNodeId'], id))[0]
    browsename = graph.object((subject, rdf_ns['base']['hasBrowseName']))[0]
    return namespace()


def add_uanode(g, node, type, xml_ns):
    namespace, classiri = add_nodeid_to_class(g, node, type, xml_ns)
    #add_references_to_class(g, node, classiri, namespace, xml_ns)

def resolve_alias(nodeid):
    alias = nodeid
    if not isNodeId(nodeid):
        alias = aliases[nodeid]
    return alias


def get_datatype(g, node, classiri):
    data_type = node.get('DataType')
    if data_type is not None:
        data_type = resolve_alias(data_type)
        dt_index, dt_id = parse_nodeid(data_type)
        g.add((classiri, rdf_ns['base']['hasDataType'], typeIds[dt_index][dt_id]))


def get_components(g, refnodes, classiri):
    for reference in refnodes:
        reftype = reference.get('ReferenceType')
        isforward = reference.get('IsForward')
        nodeid = resolve_alias(reftype)
        type_index, type_id = parse_nodeid(nodeid)
        if type_id == hasComponent and type_index == 0:
            componentId = resolve_alias(reference.text)
            index, id = parse_nodeid(componentId)
            namespace = get_rdf_ns_from_ua_index(index)
            targetclassiri = nodeId_to_iri(namespace, id)
            if isforward != 'false':
                g.add((classiri, rdf_ns['base']['hasComponent'], targetclassiri))
            else:
                g.add((targetclassiri, rdf_ns['base']['hasComponent'], classiri))


def add_typedef(g, node, xml_ns):
    _, browsename = getBrowsename(node)
    nodeid = node.get('NodeId')
    index, id = parse_nodeid(nodeid)
    namespace = get_rdf_ns_from_ua_index(index)
    classiri = nodeId_to_iri(namespace, id)
    references_node = node.find('opcua:References', xml_ns)
    references = references_node.findall('opcua:Reference', xml_ns)
    if len(references) > 0:
        get_components(g, references, classiri)
        typedef = None
        for reference in references:
            reftype = reference.get('ReferenceType')
            isforward = reference.get('IsForward')
            nodeid = resolve_alias(reftype)
            type_index, type_id = parse_nodeid(nodeid)
            if type_id == hasTypeDefinition and type_index == 0:
                # HasSubtype detected
                typedef = reference.text    
                break
        nodeid = resolve_alias(typedef)
        typedef_index, typedef_id = parse_nodeid(typedef)
        if (isforward == 'false'):
            print(f"Warning: IsForward=false makes not sense here: {classiri}")
            return
        g.add((classiri, RDF.type, typeIds[typedef_index][typedef_id])) 
    get_datatype(g, node, classiri)
    return    


def add_type(g, node, xml_ns):
    _, browsename = getBrowsename(node)
    #browsename = node.get('BrowseName')
    nodeid = node.get('NodeId')
    ref_index, ref_id = parse_nodeid(nodeid)
    ref_namespace = get_rdf_ns_from_ua_index(ref_index)
    br_namespace = ref_namespace
    #if brindex is not None and brindex != ref_index:
    #    br_namespace = get_rdf_ns_from_ua_index(brindex)
    ref_classiri = nodeId_to_iri(ref_namespace, ref_id)
    references_node = node.find('opcua:References', xml_ns)
    references = references_node.findall('opcua:Reference', xml_ns)
    g.add((ref_namespace[browsename], RDF.type, OWL.Class))
    if len(references) > 0:
        get_components(g, references, ref_classiri)
        subtype = None
        for reference in references:
            reftype = reference.get('ReferenceType')
            isforward = reference.get('IsForward')
            nodeid = resolve_alias(reftype)
            reftype_index, reftype_id = parse_nodeid(nodeid)
            if reftype_id == hasSubtypeId and reftype_index == 0:
                # HasSubtype detected
                subtype = reference.text    
                break
        nodeid = resolve_alias(subtype)
        subtype_index, subtype_id = parse_nodeid(subtype)
        typeiri = typeIds[subtype_index][subtype_id]
        if (isforward == 'false'):
            g.add((br_namespace[browsename], RDFS.subClassOf, typeiri))
        else:
            g.add((typeiri, RDFS.subClassOf, br_namespace[browsename]))
        
        isAbstract = node.get('IsAbstract')
        if isAbstract is not None:
            g.add((br_namespace[browsename], rdf_ns['base']['isAbstract'], Literal(isAbstract)))
    typeIds[ref_index][ref_id] = br_namespace[browsename]
    g.add((ref_classiri, rdf_ns['base']['definesType'], br_namespace[browsename]))
    get_datatype(g, node, ref_classiri)

    return


def get_nid_ns_and_name(g, node):
    nodeid = node.get('NodeId')
    ni_index, ni_id = parse_nodeid(nodeid)
    _, bn_name = getBrowsename(node)
    #browsename = node.get('BrowseName')
    #bn_index, bn_name = split_ns_term(browsename)
    index = ni_index
    #if bn_index is not None:
    #    index = bn_index
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
    ontology_name = URIRef(args.namespace) if args.namespace is not None else None
    ontology_prefix = args.prefix
    if args.imports is not None:
        imported_ontologies = list(map(URIRef, args.imports))
    tree = ET.parse(upcua_nodeset)
    #calling the root element
    root = tree.getroot()

    #g = Graph()

    namespace_uris = root.find('opcua:NamespaceUris', xml_ns)
    create_prefixes(g, namespace_uris)
    init_nodeids(opcua_inputs, ontology_name, ontology_prefix)
    create_header(g)
    aliases_node = root.find('opcua:Aliases', xml_ns)
    alias_nodes = aliases_node.findall('opcua:Alias', xml_ns)
    scan_aliases(alias_nodes)
    all_nodeclasses = [
        ('opcua:UADataType', 'DataTypeNodeClass'),
        ('opcua:UAVariable', 'VariableNodeClass'), 
        ('opcua:UAObjectType', 'ObjectTypeNodeClass'), 
        ('opcua:UAObject', 'ObjectNodeClass'),
        ('opcua:UAReferenceType', 'ReferenceTypeNodeClass'),
        ('opcua:UAVariableType', 'VariableTypeNodeClass')
    ]
    type_nodeclasses = [
        ('opcua:UADataType', 'DataTypeNodeClass'),
        ('opcua:UAObjectType', 'ObjectTypeNodeClass'),
        ('opcua:UAReferenceType', 'ReferenceTypeNodeClass'),
        ('opcua:UAVariableType', 'VariableTypeNodeClass')
    ]
    typed_nodeclasses = [
        ('opcua:UAVariable', 'VariableNodeClass'), 
        ('opcua:UAObject', 'ObjectNodeClass')
    ]
    # Add Basic definition of NodeClasses
    for tag_name, type in all_nodeclasses:
        uanodes = root.findall(tag_name, xml_ns)   
        for uanode in uanodes:
            add_uanode(g, uanode, type, xml_ns)
    # Create Type Hierarchy
    for tag_name, _ in type_nodeclasses:
        uanodes = root.findall(tag_name, xml_ns)   
        for uanode in uanodes:
            add_type(g, uanode, xml_ns)
    # Type objects and varialbes
    for tag_name, _ in typed_nodeclasses:
        uanodes = root.findall(tag_name, xml_ns)   
        for uanode in uanodes:
            add_typedef(g, uanode, xml_ns)
        
    # Process all nodes by type
    uadatatypes = root.findall('opcua:UADataType', xml_ns)
    for uadatatype in uadatatypes:
        add_uadatatype(g, uadatatype, xml_ns)

    # uavariables = root.findall('opcua:UAVariable', xml_ns)
    # for uavariable in uavariables:
    #     add_uavariable(g, uavariable)

    # uaobjecttypes = root.findall('opcua:UAObjectType', xml_ns)
    # for uaobjecttype in uaobjecttypes:
    #     add_uaobjecttype(g, uaobjecttype)
        
    write_graph(g, opcua_output)