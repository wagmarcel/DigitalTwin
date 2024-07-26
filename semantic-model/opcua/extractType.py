import sys
import os
import pathlib
from urllib.parse import urlparse
import json
import random
import string
import functools
import urllib
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS, SH, XSD
import argparse


query_namespaces = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?uri ?prefix ?ns WHERE {
    ?ns rdf:type base:Namespace .
    ?ns base:hasUri ?uri .
    ?ns base:hasPrefix ?prefix .
}
"""

query_enumclass = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

CONSTRUCT { ?s ?p ?o .
            ?c ?classpred ?classobj .
			?o2 base:hasEnumValue ?value .
			?o2 base:hasValueClass ?class .
}
WHERE
 { 
  ?s ?p ?o .
  ?s rdf:type ?c .
  ?c ?classpred ?classobj .
  ?s ?p2 ?o2 .
  ?o2 a base:ValueNode .
  ?o2 base:hasEnumValue ?value .
  ?o2 base:hasValueClass ?class .
}
"""

query_default_instance = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?instance WHERE {
  	?instance a ?c .
    ?instance base:hasValueNode ?valueNode .
  	?valueNode 	base:hasEnumValue ?value .
} order by ?value limit 1
"""

query_instance = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?instance WHERE {
  	?instance a ?c .
    ?instance base:hasValueNode ?valueNode .
  	?valueNode 	base:hasEnumValue ?value .
}
"""

randnamelength = 16
modelling_nodeid_optional = 80
modelling_nodeid_mandatory = 78
modelling_nodeid_optional_array = 11508
basic_types = ['String', 'Boolean', 'Byte', 'SByte', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Uin64', 'Int64', 'Float', 'DateTime', 'Guid', 'ByteString', 'Double']


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type', help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parser.add_argument('-j', '--jsonld', help='Filename of jsonld output file', required=False, default='entities.jsonld')
    parser.add_argument('-e', '--entities', help='Filename of entities output file', required=False, default='entities.ttl')
    parser.add_argument('-s', '--shacl', help='Filename of SHACL output file', required=False, default='shacl.ttl')
    parser.add_argument('-k', '--knowledge', help='Filename of SHACL output file', required=False, default='knowledge.ttl')
    parser.add_argument('-b', '--bindings', help='Filename of bindings output file', required=False, default='bindings.ttl')
    parser.add_argument('-c', '--context', help='Filename of JSONLD context output file', required=False, default='context.jsonld')
    parser.add_argument('-d', '--debug', help='Add additional debug info to structure (e.g. for better SHACL debug)', required=False, action='store_true')
    parser.add_argument('-m', '--minimalshacl', help='Remove all not monitored/updated shacl nodes', required=False, action='store_true')
    parser.add_argument('-n', '--namespace', help='Namespace prefix for entities, SHACL and JSON-LD', required=True)
    parser.add_argument('-i', '--id', help='ID prefix of object. The ID for every object is generated by "urn:<prefix>:nodeId"', required=False, default="testid")
    
    parsed_args = parser.parse_args(args)
    return parsed_args

basens = None # Will be defined by the imported ontologies
opcuans = None # dito
ngsildns = Namespace('https://uri.etsi.org/ngsi-ld/')
instances = []


def isNodeclass(type):
    nodeclasses = [opcuans['BaseNodeClass'], opcuans['DataTypeNodeClass'], opcuans['ObjectNodeClass'], opcuans['ObjectTypeNodeClass'], opcuans['ReferenceTypeNodeClass'], opcuans['VariableNodeClass'], opcuans['VariableNodeClass']]
    result = bool([ele for ele in nodeclasses if(ele == type)])
    return result


def isObjectNodeClass(type):
    return type == opcuans['ObjectNodeClass']


def isVariableNodeClass(type):
    return type == opcuans['VariableNodeClass']

def attributename_from_type(type):
    basename = None
    url = urlparse(type)
    if url.path is not None:
        basename = os.path.basename(url.path)
        basename = basename.removesuffix('Type')
    return basename

def get_type(node):
    nc = None
    type = None
    for typenc in g.objects(node, RDF.type):
        if isNodeclass(typenc):
            nc = typenc
        elif typenc != OWL.NamedIndividual:
            type = typenc
    return nc, type


def map_datatype_to_jsonld(data_type):
    boolean_types = [opcuans['Boolean']]
    integer_types = [opcuans['Integer'], opcuans['Int16'], opcuans['Int32'], opcuans['Int64'], opcuans['SByte'],
                     opcuans['UInteger'], opcuans['UInt16'], opcuans['UInt32'], opcuans['UInt64'], opcuans['Byte']]
    number_types = [opcuans['Decimal'], opcuans['Double'], opcuans['Duration'], opcuans['Float']]
    if data_type in boolean_types:
        return XSD.boolean
    if data_type in integer_types:
        return XSD.integer
    if data_type in number_types:
        return XSD.double
    return XSD.string


def get_shacl_iri_and_contentclass(g, node, shacl_rule, attribute_name):
    try:
        data_type = next(g.objects(node, basens['hasDatatype']))
        shacl_rule['datatype'] = map_datatype_to_jsonld(data_type)
        base_data_type = next(g.objects(data_type, RDFS.subClassOf))
        e.add((attribute_name, basens['hasOPCUADatatype'], data_type))
        if base_data_type != opcuans['Enumeration']:
            shacl_rule['is_iri'] = False
            shacl_rule['contentclass'] = None
        else:
            shacl_rule['is_iri'] = True
            shacl_rule['contentclass'] = data_type
    except:
        shacl_rule['is_iri'] = False
        shacl_rule['contentclass'] = None


def get_default_value(datatype):
    if datatype == XSD.integer:
        return 0
    if datatype == XSD.double:
        return 0.0
    if datatype == XSD.string:
        return ''
    if datatype == XSD.boolean:
        return False
    print(f'Warning: unknown default value for datatype {datatype}')


def get_default_contentclass(knowledgeg, contentclass):
    bindings = {'c': contentclass}
    result = knowledgeg.query(query_default_instance, initBindings=bindings, initNs={'base': basens, 'opcua': opcuans})
    foundclass = None
    if len(result) > 0:
        foundclass = list(result)[0].instance
    if foundclass is None:
        print(f'Warning: no default instance found for class {contentclass}')
    return foundclass


def get_contentclass(knowledgeg, contentclass, value):
    bindings = {'c': contentclass, 'value': value}
    result = knowledgeg.query(query_instance, initBindings=bindings, initNs={'base': basens, 'opcua': opcuans})
    foundclass = None
    if len(result) > 0:
        foundclass = list(result)[0].instance
    if foundclass is None:
        print(f'Warning: no instance found for class {contentclass} with value {value}')
    return foundclass


def generate_node_id(node, id, instancetype):
    try:
        node_id = next(g.objects(node, basens['hasNodeId']))
        idtype = next(g.objects(node, basens['hasIdentifierType']))
        bn = next(g.objects(rootentity, basens['hasBrowseName']))
    except:
        node_id = 'unknown'
    idt = idtype2String(idtype)
    if instancetype == rootinstancetype:
        return f'{id}:{bn}'
    else:
        return f'{id}:{bn}:sub:{idt}{node_id}'


def idtype2String(idtype):
    if idtype == basens['numericID']:
        idt = 'i'
    elif idtype == basens['stringID']:
        idt = 's'
    elif idtype == basens['guidID']:
        idt = 'g'
    elif idtype == basens['opaqueID']:
        idt = 'b'
    else:
        idt = 'x'
        print(f'Warning no idtype found.')
    return idt


def create_binding(g, bindingsg, parent_node_id, var_node, attribute_iri, version='0.1', firmware='firmware'):
    randname = ''.join(random.choices(string.ascii_uppercase + string.digits, k=randnamelength))
    bindingiri = binding_namespace[f'binding_' + randname]
    mapiri = binding_namespace[f'map_' + randname]
    dtype = next(g.objects(var_node, basens['hasDatatype']))
    node_id = next(g.objects(var_node, basens['hasNodeId']))
    idtype = next(g.objects(var_node, basens['hasIdentifierType']))
    ns = next(g.objects(var_node, basens['hasNamespace']))
    nsuri = next(g.objects(ns, basens['hasUri']))
    
    bindingsg.add((bindingiri, RDF['type'], basens['Binding']))
    bindingsg.add((bindingiri, basens['bindsEntity'], parent_node_id))
    bindingsg.add((bindingiri, basens['bindingVersion'], Literal(version)))
    bindingsg.add((bindingiri, basens['bindsFirmware'], Literal(firmware)))
    bindingsg.add((bindingiri, basens['bindsMap'], mapiri))
    bindingsg.add((attribute_iri, basens['boundBy'], bindingiri))
    bindingsg.add((mapiri, RDF['type'], basens['BoundMap']))
    bindingsg.add((mapiri, basens['bindsConnector'], basens['OPCUAConnector']))
    bindingsg.add((mapiri, basens['bindsMapDatatype'], dtype))
    bindingsg.add((mapiri, basens['bindsLogicVar'], Literal('var1')))
    bindingsg.add((mapiri, basens['bindsConnectorParameter'], Literal(f'nsu={nsuri};{idtype2String(idtype)}={node_id}')))
    

def scan_type(node, instancetype):
    # Loop through all components
    shapename = create_shacl_type(instancetype)
    print(shapename)
    components = g.triples((node, basens['hasComponent'], None))
    addins = g.triples((node, basens['hasAddIn'], None))
    #components = list(components) + list(addins)
    has_components = False
    for (_, _, o) in components:
        has_components = scan_type_recursive(o, node, instancetype, shapename) or has_components
    addins = g.triples((node, basens['hasAddIn'], None))
    for (_, _, o) in addins:
        has_components = scan_type_recursive(o, node, instancetype, shapename) or has_components
    organizes = g.triples((node, basens['organizes'], None))
    for (_, _, o) in organizes:
        scan_type_nonrecursive(o, node, instancetype, shapename)
        has_components = True
    return has_components


def scan_type_recursive(o, node, instancetype, shapename):
    has_components = False
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    #print(f'Processing Node {o} with browsename {browse_name}')
    nodeclass, classtype = get_type(o)
    attributename = urllib.parse.quote(f'has{browse_name}')
    if len(list(e.objects(entity_namespace[attributename], RDF.type))) > 0:
        return has_components
    shacl_rule['path'] = entity_namespace[attributename]
    get_modelling_rule(node, shacl_rule)
    e.add((entity_namespace[attributename], RDF.type, OWL.ObjectProperty))
    e.add((entity_namespace[attributename], RDFS.domain, URIRef(instancetype)))
    e.add((entity_namespace[attributename], RDF.type, OWL.NamedIndividual))
    e.add((entity_namespace[attributename], RDF.type, basens['SubComponentRelationship']))
    types.append(classtype)
    
    if isObjectNodeClass(nodeclass):
        shacl_rule['is_property'] = False
        e.add((entity_namespace[attributename], RDFS.range, ngsildns['Relationship']))
        _, use_instance_declaration = get_modelling_rule(o, None)
        if use_instance_declaration:
            # This information mixes two details
            # 1. Use the instance declaration and not the object for instantiation
            # 2. It could be zero or more instances (i.e. and array)
            shacl_rule['array'] = True
            _, typeiri = get_type(o)
            try:
                typenode = next(g.subjects(basens['definesType'], typeiri))
                o = typenode
            except:
                pass
        components_found = scan_type(o, classtype)
        if components_found:
            has_components = True
            shacl_rule['contentclass'] = classtype
            create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], False, True, shacl_rule['contentclass'], None)
    elif isVariableNodeClass(nodeclass):
        has_components = True
        shacl_rule['is_property'] = True
        e.add((entity_namespace[attributename], RDFS.range, ngsildns['Property']))
        get_shacl_iri_and_contentclass(g, o, shacl_rule, entity_namespace[attributename])
        create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], True, shacl_rule['is_iri'], shacl_rule['contentclass'], shacl_rule['datatype'])
        add_class_to_knowledge(g, knowledgeg, shacl_rule['contentclass'])
    return has_components


def scan_type_nonrecursive(o, node, instancetype, shapename):
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    #print(f'Processing Node {o} with browsename {browse_name}')
    nodeclass, classtype = get_type(o)
    attributename = urllib.parse.quote(f'has{browse_name}')
    shacl_rule['path'] = entity_namespace[attributename]
    get_modelling_rule(node, shacl_rule)
    e.add((entity_namespace[attributename], RDF.type, OWL.ObjectProperty))
    e.add((entity_namespace[attributename], RDFS.domain, URIRef(instancetype)))
    e.add((entity_namespace[attributename], RDF.type, OWL.NamedIndividual))
    #e.add((entity_namespace[attributename], RDF.type, basens['SubComponentRelationship']))
    types.append(classtype)
    
    if isObjectNodeClass(nodeclass):
        shacl_rule['is_property'] = False
        e.add((entity_namespace[attributename], RDFS.range, ngsildns['Relationship']))
        shacl_rule['contentclass'] = classtype
        create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], False, True, shacl_rule['contentclass'], None)
    elif isVariableNodeClass(nodeclass):
        shacl_rule['is_property'] = True
        e.add((entity_namespace[attributename], RDFS.range, ngsildns['Property']))
        get_shacl_iri_and_contentclass(g, o, shacl_rule, entity_namespace[attributename])
        create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], True, shacl_rule['is_iri'], shacl_rule['contentclass'], shacl_rule['datatype'])
        add_class_to_knowledge(g, knowledgeg, shacl_rule['contentclass'])
    return


def get_modelling_rule(node, shacl_rule):
    use_instance_declaration = False
    is_optional = True
    try:
        modelling_node = next(g.objects(node, basens['hasModellingRule']))
        modelling_rule = next(g.objects(modelling_node, basens['hasNodeId']))
        if int(modelling_rule) == modelling_nodeid_optional:
            is_optional = True
        elif int(modelling_rule) == modelling_nodeid_mandatory:
            is_optional = False
        else:
            is_optional = True
        if int(modelling_rule) == modelling_nodeid_optional_array:
            is_optional = True
            use_instance_declaration = True
        else:
            is_optional = False
    except:
        pass
    if shacl_rule is not None:
        shacl_rule['optional'] = is_optional
        shacl_rule['array'] = use_instance_declaration
    return is_optional, use_instance_declaration


def scan_entity(node, instancetype, id):
    #instancetype = next(g.objects(node, RDF.type))
    node_id = generate_node_id(node, id, instancetype)
    instance = {}
    instance['type'] = instancetype
    instance['id'] = node_id
    instance['@context'] = [
        "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld", {
            "uaentities": {
                "@id": entity_namespace,
                "@prefix": True
            }
        }]

    # Loop through all components
    #shapename = create_shacl_type(instancetype)
    has_components = False
    components = g.triples((node, basens['hasComponent'], None))
    for (s, p, o) in components:
        shacl_rule = {}
        browse_name = next(g.objects(o, basens['hasBrowseName']))
        #print(f'Processing Node {o} with browsename {browse_name}')
        nodeclass, classtype = get_type(o)
        attributename = urllib.parse.quote(f'has{browse_name}')
        shacl_rule['path'] = entity_namespace[attributename]
        try:
            modelling_node = next(g.objects(node, basens['hasModellingRule']))
            modelling_rule = next(g.objects(modelling_node, basens['hasNodeId']))
            if int(modelling_rule) == modelling_nodeid_optional:
                shacl_rule['optional'] = True
            elif int(modelling_rule) == modelling_nodeid_mandatory:
                shacl_rule['optional'] = False
            else:
                shacl_rule['optional'] = True
        except:
            shacl_rule['optional'] = True
        types.append(classtype)
       
        if isObjectNodeClass(nodeclass):
            shacl_rule['is_property'] = False
            #relid = f'{id}:{idadd}'
            relid = scan_entity(o, classtype, id)
            if relid is not None:
                has_components = True
                instance[f'uaentities:{attributename}'] = {
                    'type': 'Relationship',
                    'object': relid
                }
                if debug:
                    instance[f'uaentities:{attributename}']['debug'] = f'uaentities:{attributename}'
                shacl_rule['contentclass'] = classtype
                #create_ngsild_object(o, type, f'{id}:{idadd}')
                # create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], False, True, shacl_rule['contentclass'], None)
        elif isVariableNodeClass(nodeclass):
            shacl_rule['is_property'] = True
            get_shacl_iri_and_contentclass(g, o, shacl_rule, entity_namespace[attributename])
            try:
                value = next(g.objects(o, basens['hasValue']))
                if not shacl_rule['is_iri']:
                    value = value.toPython()
                else:
                    value = get_contentclass(knowledgeg, shacl_rule['contentclass'], value)
                    
                    value = value.toPython()
            except StopIteration:
                if not shacl_rule['is_iri']:
                    value = get_default_value(shacl_rule['datatype'])
                else:
                    value = get_default_contentclass(knowledgeg, shacl_rule['contentclass'])
            has_components = True
            if not shacl_rule['is_iri']:
                instance[f'uaentities:{attributename}'] = {
                    'type': 'Property',
                    'value': value
                }
            else:
                instance[f'uaentities:{attributename}'] = {
                    'type': 'Property',
                    'value': { '@id': str(value)}
                }
            if debug:
                instance[f'uaentities:{attributename}']['debug'] = f'uaentities:{attributename}'
            try:
                is_updating = bool(next(g.objects(o, basens['isUpdating'])))
            except:
                is_updating = False
            if is_updating:
                create_binding(g, bindingsg, URIRef(node_id), o, entity_namespace[attributename])
                #print(f"Now binding {attributename} to {node}")
    if has_components:
        instances.append(instance)
        return node_id
    else:
        return None


def get_typename(url):
    result = urlparse(url)
    if result.fragment != '':
        return result.fragment 
    else:
        basename = os.path.basename(result.path)
        return basename


def create_shacl_type(targetclass):
    global shaclg
    name = get_typename(targetclass) + 'Shape' 
    shapename = shacl_namespace[name]
    shaclg.add((shapename, RDF.type, SH.NodeShape))
    shaclg.add((shapename, SH.targetClass, URIRef(targetclass)))
    return shapename


def create_shacl_property(shapename, path, optional, is_property, is_iri, contentclass, datatype):
    global shaclg
    innerproperty = BNode()
    property = BNode()
    maxCount = 1
    minCount = 1
    if optional:
        minCount = 0
    shaclg.add((shapename, SH.property, property))    
    shaclg.add((property, SH.path, path))
    shaclg.add((property, SH.nodeKind, SH.BlankNode))
    shaclg.add((property, SH.minCount, Literal(minCount)))
    shaclg.add((property, SH.maxCount, Literal(maxCount)))
    shaclg.add((property, SH.property, innerproperty))
    if is_property:
        shaclg.add((innerproperty, SH.path, ngsildns['hasValue']))
    else:
        shaclg.add((innerproperty, SH.path, ngsildns['hasObject']))
    if is_iri:
        shaclg.add((innerproperty, SH.nodeKind, SH.IRI))
        if contentclass is not None:
            shaclg.add((innerproperty, SH['class'], contentclass))
    elif is_property:
        shaclg.add((innerproperty, SH.nodeKind, SH.Literal))
        if datatype is not None:
            shaclg.add((innerproperty, SH.datatype, datatype))

    shaclg.add((innerproperty, SH.minCount, Literal(1)))
    shaclg.add((innerproperty, SH.maxCount, Literal(1)))
    

def add_class_to_knowledge(g, knowledgeg, contentclass):
    if contentclass == None or not isinstance(contentclass, URIRef):
        return
    bindings = {'c': contentclass}
    print(f'Adding type {contentclass} to knowledge.')
    result = g.query(query_enumclass, initBindings=bindings, initNs={'base': basens, 'opcua': opcuans})
    #result = g.triples((contentclass, None, None))
    #for s, p, o in result:
    #    knowledgeg.add((s, p, o))
    knowledgeg += result


def create_ontolgoy_header(g, entity_namespace, version=0.1, versionIRI=None):
    g.add((URIRef(entity_namespace), RDF.type, OWL.Ontology))
    if versionIRI is not None:
        g.add((URIRef(entity_namespace), OWL.versionIRI, versionIRI))
    g.add((URIRef(entity_namespace), OWL.versionInfo, Literal(0.1)))


def extract_namespaces(graph):
    return {
        prefix: {
            '@id': str(namespace),
            '@prefix': True
            } for prefix, namespace in graph.namespaces()}


if __name__ == '__main__':

    args = parse_args()
    instancename = args.instance
    rootinstancetype = args.type
    jsonldname = args.jsonld
    entitiesname = args.entities
    shaclname = args.shacl
    knowledgename = args.knowledge
    bindingsname = args.bindings
    contextname = args.context
    debug = args.debug
    namespace_prefix = args.namespace
    entity_namespace = Namespace(f'{namespace_prefix}entities/')
    shacl_namespace = Namespace(f'{namespace_prefix}shacl/')
    knowledge_namespace = Namespace(f'{namespace_prefix}knowledge/')
    binding_namespace = Namespace(f'{namespace_prefix}bindings/')
    entity_id = args.id
    g = Graph(store='Oxigraph')
    #g = Graph()
    g.parse(instancename)
    # get all owl imports
    mainontology = next(g.subjects(RDF.type, OWL.Ontology))
    imports = g.objects(mainontology, OWL.imports)
    for imprt in imports:
        h = Graph(store="Oxigraph")
        print(f'Importing ontology {imprt}')
        h.parse(imprt)
        g += h
        for k, v in list(h.namespaces()):
            g.bind(k, v)

    e = Graph()
    shaclg = Graph()
    knowledgeg = Graph()
    bindingsg = Graph()
    types = []
    e.bind('entities', entity_namespace)
    shaclg.bind('shacl', shacl_namespace)
    e.bind('ngsi-ld', ngsildns)
    create_ontolgoy_header(e, entity_namespace)

    shaclg.bind('ngsi-ld', ngsildns)

    shaclg.bind('sh', SH)
    knowledgeg.bind('knowledge', knowledge_namespace)
    bindingsg.bind('entities', entity_namespace)
  
    for k, v in list(g.namespaces()):
        knowledgeg.bind(k, v)
    basens = next(Namespace(uri) for prefix, uri in list(knowledgeg.namespaces()) if prefix == 'base')
    opcuans = next(Namespace(uri) for prefix, uri in list(knowledgeg.namespaces()) if prefix == 'opcua')
    bindingsg.bind('base', basens)
    bindingsg.bind('binding', binding_namespace)
    shaclg.bind('base', basens)
    e.bind('base', basens)

    #create_shacl_type(s, instancetype)
    result = g.query(query_namespaces, initNs={'base': basens, 'opcua': opcuans})
    for uri, prefix, _ in result:
        e.bind(prefix, Namespace(uri))
    # First scan the templates to create the rules
    root = next(g.subjects(basens['definesType'], URIRef(rootinstancetype)))
    scan_type(root, rootinstancetype)
    # Then scan the entity with the real values
    rootentity = next(g.subjects(RDF.type, URIRef(rootinstancetype)))
    scan_entity(rootentity, rootinstancetype, entity_id)
    # Add types to entities
    for type in types:
        e.add((type, RDF.type, OWL.Class))
        e.add((type, RDF.type, OWL.NamedIndividual))
        e.add((type, RDFS.subClassOf, opcuans['BaseObjectType']))
    if jsonldname is not None:
        with open(jsonldname, 'w') as f:
            json.dump(instances, f, ensure_ascii=False, indent=4)
    if entitiesname is not None:
        e.serialize(destination=entitiesname)
    if shaclname is not None:
        shaclg.serialize(destination=shaclname)
    if len(knowledgeg) > 0:
        knowledgeg.serialize(destination=knowledgename)
    entities_ns = extract_namespaces(e)
    shacl_ns = extract_namespaces(shaclg)
    knowledge_ns = extract_namespaces(knowledgeg)
    combined_namespaces = {**entities_ns, **shacl_ns, **knowledge_ns}
    jsonld_context = {
        "@context": combined_namespaces
    }
    with open(contextname, "w") as f:
        json.dump(jsonld_context, f, indent=2)
    if len(bindingsg) > 0:
        bindingsg.serialize(destination=bindingsname)

