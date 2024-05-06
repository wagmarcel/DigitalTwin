import sys
import os
import pathlib
import json
import functools
import urllib
from urllib.parse import urlparse
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


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type', help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parser.add_argument('-j', '--jsonld', help='Filename of jsonld output file', required=False)
    parser.add_argument('-e', '--entities', help='Filename of entities output file', required=False)
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
    for (s, p, o) in g.triples((node, basens['hasComponent'], None)):
        browse_name = next(g.objects(o, basens['hasBrowseName']))
        print(f'Processing Node {o} with browsename {browse_name}')
        nodeclass, type = get_type(o)
        attributename = urllib.parse.quote(f'has{browse_name}')
        e.add((entity_namespace[attributename], RDF.type, OWL.ObjectProperty))
        e.add((entity_namespace[attributename], RDFS.domain, type))
        e.add((entity_namespace[attributename], RDF.type, OWL.NamedIndividual))
        types.append(type)
        if isObjectNodeClass(nodeclass):
            e.add((entity_namespace[attributename], RDFS.range, ngsildns['Relationship']))
            relid = f'{id}:{idadd}'
            create_ngsild_object(o, type, relid)
            instance[attributename] = {
                'Property': 'Relationship',
                'object': relid
            }
            #create_ngsild_object(o, type, f'{id}:{idadd}')
            idadd += 1
        elif isVariableNodeClass(nodeclass):
            e.add((entity_namespace[attributename], RDFS.range, ngsildns['Property']))
            try:
                value = next(g.objects(o, basens['hasValue']))
            except StopIteration:
                value = ''
            instance[attributename] = {
                'Property': 'Property',
                'value': value
            }
        #for type in g.objects(o, RDF.type):
        print(nodeclass, type)
    for (s, p, o) in g.triples((node, basens['hasProperty'], None)):
        browse_name = next(g.objects(o, basens['hasBrowseName']))
        print(f'Processing Node {o} with browsename {browse_name}')
        nodeclass, type = get_type(o)
        attributename = f'has{browse_name}'
        if isVariableNodeClass(nodeclass):
            try:
                value = next(g.objects(o, basens['hasValue']))
            except StopIteration:
                value = ''
        instance[attributename] = {
            'Property': 'Property',
            'value': value
        }
    instances.append(instance)


if __name__ == '__main__':
    args = parse_args()
    instancename = args.instance
    instancetype = args.type
    jsonldname = args.jsonld
    entitiesname = args.entities
    namespace_prefix = args.namespace
    entity_namespace = Namespace(f'{namespace_prefix}entities/')
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
    types = []
    e.bind('entities', entity_namespace)
    e.bind('ngsild', ngsildns)
    result = g.query(query_namespaces)
    for uri, prefix, _ in result:
        e.bind(prefix, Namespace(uri))
    root = next(g.subjects(RDF.type, URIRef(instancetype)))
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

        