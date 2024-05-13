import sys
import os
import pathlib
from urllib.parse import urlparse
import json
import functools
import urllib
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS, SH
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
modelling_nodeid_optional = 80
modelling_nodeid_mandatory = 78
basic_types = ['String', 'Boolean', 'Byte', 'SByte', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Uin64', 'Int64', 'Float', 'DateTime', 'Guid', 'ByteString', 'Double']

def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type', help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parser.add_argument('-j', '--jsonld', help='Filename of jsonld output file', required=False)
    parser.add_argument('-e', '--entities', help='Filename of entities output file', required=False)
    parser.add_argument('-s', '--shacl', help='Filename of shacl output file', required=False)
    parser.add_argument('-n', '--namespace', help='Namespace prefix for entities, SHACL and JSON-LD', required=True)
    parsed_args = parser.parse_args(args)
    return parsed_args

basens = Namespace('http://opcfoundation.org/UA/Base/')
opcuans = Namespace('http://opcfoundation.org/UA/')
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
        else:
            type = typenc
    return nc, type


def create_ngsild_object(node, instancetype, id):
    #instancetype = next(g.objects(node, RDF.type))
    instance = {}
    instance['type'] = instancetype
    instance['id'] = id
    instance['@context'] = {}


    # Loop through all components
    idadd = 0
    shapename = create_shacl_type(instancetype)
    for (s, p, o) in g.triples((node, basens['hasComponent'], None)):
        shacl_rule = {}
        browse_name = next(g.objects(o, basens['hasBrowseName']))
        print(f'Processing Node {o} with browsename {browse_name}')
        nodeclass, type = get_type(o)
        attributename = urllib.parse.quote(f'has{browse_name}')
        shacl_rule['path'] = entity_namespace[attributename]
        try:
            modelling_node = next(g.objects(node, basens['hasModellingRule']))
            modelling_rule = next(g.objects(modelling_node, basens['hasNodeId']))
            if int(modelling_rule) == modelling_nodeid_optional:
                shacl_rule['optional'] = True
            elif int(modelling_rule) == modelling_nodeid_mandatory:
                shacl_rule['optional'] = False                
        except:
            shacl_rule['optional'] = True
        e.add((entity_namespace[attributename], RDF.type, OWL.ObjectProperty))
        e.add((entity_namespace[attributename], RDFS.domain, URIRef(instancetype)))
        e.add((entity_namespace[attributename], RDF.type, OWL.NamedIndividual))
        e.add((entity_namespace[attributename], RDF.type, basens['SubComponentRelationship']))
        types.append(type)
       
        if isObjectNodeClass(nodeclass):
            shacl_rule['is_property'] = False
            e.add((entity_namespace[attributename], RDFS.range, ngsildns['Relationship']))
            relid = f'{id}:{idadd}'
            create_ngsild_object(o, type, relid)
            instance[attributename] = {
                'Property': 'Relationship',
                'object': relid
            }
            shacl_rule['contentclass'] = type
            #create_ngsild_object(o, type, f'{id}:{idadd}')
            idadd += 1
            create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], False, True, shacl_rule['contentclass'])
        elif isVariableNodeClass(nodeclass):
            shacl_rule['is_property'] = True
            e.add((entity_namespace[attributename], RDFS.range, ngsildns['Property']))
            try:
                value = next(g.objects(o, basens['hasValue']))
            except StopIteration:
                value = ''
            instance[attributename] = {
                'Property': 'Property',
                'value': value
            }                
            try:
                data_type = next(g.objects(o, basens['hasDataType']))
                print(data_type)
                base_data_type = next(g.objects(data_type, RDFS.subClassOf))
                if base_data_type != opcuans['Enumeration']:
                    shacl_rule['is_iri'] = False
                else:
                    shacl_rule['is_iri'] = True
                    shacl_rule['contentclass'] = base_data_type
            except:
                pass
        #for type in g.objects(o, RDF.type):
        print(nodeclass, type)
    for (s, p, o) in g.triples((node, basens['hasProperty'], None)):
        browse_name = next(g.objects(o, basens['hasBrowseName']))
        print(f'Processing Node {o} with browsename {browse_name}')
        nodeclass, type = get_type(o)
        attributename = f'has{browse_name}'
        if isVariableNodeClass(nodeclass):
            try:
                value = next(g.objects(o, basens['hasProperty']))
            except StopIteration:
                value = ''
        instance[attributename] = {
            'Property': 'Property',
            'value': value
        }
        shacl_rule['is_property'] = True
        #e.add((entity_namespace[attributename], RDFS.range, basens['OPCUAProperty']))
    instances.append(instance)


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


def create_shacl_property(shapename, path, optional, is_property, is_iri, contentclass):
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

    shaclg.add((innerproperty, SH.minCount, Literal(1)))
    shaclg.add((innerproperty, SH.maxCount, Literal(1)))
    

if __name__ == '__main__':
    args = parse_args()
    instancename = args.instance
    instancetype = args.type
    jsonldname = args.jsonld
    entitiesname = args.entities
    shaclname = args.shacl
    namespace_prefix = args.namespace
    entity_namespace = Namespace(f'{namespace_prefix}entities/')
    shacl_namespace = Namespace(f'{namespace_prefix}shacl/')
    g = Graph()
    g.parse(instancename)
    # get all owl imports
    mainontology = next(g.subjects(RDF.type, OWL.Ontology))
    imports = g.objects(mainontology, OWL.imports)
    for imprt in imports:
        h = Graph()
        h.parse(imprt)
        g += h
    e = Graph()
    shaclg = Graph()
    types = []
    e.bind('entities', entity_namespace)
    shaclg.bind('shacl', shacl_namespace)
    e.bind('ngsild', ngsildns)
    e.bind('base', basens)
    shaclg.bind('ngsild', ngsildns)
    shaclg.bind('base', basens)
    shaclg.bind('sh', SH)
    #create_shacl_type(s, instancetype)
    result = g.query(query_namespaces)
    for uri, prefix, _ in result:
        e.bind(prefix, Namespace(uri))
    root = next(g.subjects(basens['definesType'], URIRef(instancetype)))
    create_ngsild_object(root, instancetype, 'urn:test:1')
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

        