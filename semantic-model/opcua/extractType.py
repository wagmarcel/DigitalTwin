import sys
import xml.etree.ElementTree as ET
import pathlib
import json
import functools
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.namespace import OWL, RDF, RDFS
import argparse


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type', help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/', required=True)
    parsed_args = parser.parse_args(args)
    return parsed_args



if __name__ == '__main__':
    args = parse_args()
    instancename = args.instance
    instancetype = args.type
    g = Graph()
    instances = []
    g.parse(instancename)
    for root in g.subjects(RDF.type, URIRef(instancetype)):
        instance = {}
        instance['type'] = instancetype
        instance['id'] = 'urn:test:1'
        instance['@context'] = {}
        instances.append(instance)
    json.dump(instances, sys.stdout, indent=4)    

        