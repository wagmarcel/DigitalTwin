import sys
import os
import pathlib
import json
import functools
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS
import argparse


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type', help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parser.add_argument('-j', '--jsonld', help='Filename of jsonld output file', required=False)
    parsed_args = parser.parse_args(args)
    return parsed_args

basens = Namespace('http://opcfoundation.org/UA/Base/')
opcuans = Namespace('http://opcfoundation.org/UA/')
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
        attributename = f'has{browse_name}'
        if isObjectNodeClass(nodeclass):
            relid = f'{id}:{idadd}'
            create_ngsild_object(o, type, relid)
            instance[attributename] = {
                'Property': 'Relationship',
                'object': relid
            }
            #create_ngsild_object(o, type, f'{id}:{idadd}')
            idadd += 1
        elif isVariableNodeClass(nodeclass):
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
    instances.append(instance)


if __name__ == '__main__':
    args = parse_args()
    instancename = args.instance
    instancetype = args.type
    jsonldname = args.jsonld
    g = Graph()
    g.parse(instancename)
    root = next(g.subjects(RDF.type, URIRef(instancetype)))
    create_ngsild_object(root, instancetype, 'urn:test:1')
        # instance = {}
        # instance['type'] = instancetype
        # instance['id'] = 'urn:test:1'
        # instance['@context'] = {}
        # # Loop through all components
        # for (s, p, o) in g.triples((root, basens['hasComponent'], None)):
        #     browse_name = next(g.objects(o, basens['hasBrowseName']))
        #     print(f'Processing Node {o} with browsename {browse_name}')
        #     nodeclass, type = get_type(o)
        #     if isObjectNodeClass(nodeclass):
        #         attributename = f'has{attributename_from_type(type)}'
        #         instance[attributename] = {
        #             'Property': 'Relationship',
        #             'object': ''
        #         }
        #     print(nodeclass, type)
            
    if jsonldname is not None:
        with open(jsonldname, 'w') as f:
            json.dump(instances, f, ensure_ascii=False, indent=4)    

        