from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS
import owlrl
import os
import sys
import re
import datetime
import argparse
from urllib.parse import urlparse
import ruamel.yaml
import lib.utils as utils
import lib.configs as configs
from ruamel.yaml.scalarstring import (DoubleQuotedScalarString as dq, 
                                      SingleQuotedScalarString as sq)


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='create_ngsild_models.py \
                                                  <shacl.ttl> <knowledge.ttl> <model.jsonld>')

    parser.add_argument('shaclfile', help='Path to the SHACL file')
    parser.add_argument('knowledgefile', help='Path to the knowledge file')
    parser.add_argument('modelfile', help='Path to the model file')
    parsed_args = parser.parse_args(args)
    return parsed_args


attributes_query = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT (?a as ?entityId) (?b as ?name) (?e as ?type) (?d as ?nodeType) (datatype(?g) as ?valueType) (?f as ?hasValue) (?g as ?hasObject)
#SELECT ?a ?b ?c ?d
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?class .
    ?a a ?class .
    {?a ?b [ ngsild:hasObject ?g ] . 
    VALUES ?d { '@id'} . 
    VALUES ?e {ngsild:Relationship}
    } 
    UNION
    { ?a ?b [ ngsild:hasValue ?f ] .
    VALUES ?d {'@value'} . 
    VALUES ?e {ngsild:Property}
    FILTER(!isIRI(?f))
    }
    UNION
    { ?a ?b [ ngsild:hasValue ?f ] .
    VALUES ?d {'@id'} . 
    VALUES ?e {ngsild:Property}
    FILTER(isIRI(?f))
    }
    ?nodeshape sh:property [ sh:path ?b ] .
}
"""

ngsild_tables_query = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT ?id ?type ?field ?ord
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?type .
    ?id a ?type .
    ?nodeshape sh:property [ sh:path ?field ; sh:order ?ord ] .
    }
    ORDER BY ?id ?ord
"""

ngsild_tables_query_noinference = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT DISTINCT ?id ?type ?field ?ord ?shacltype
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?shacltype .
    ?id a ?type .
    ?type rdfs:subClassOf* ?shacltype .
    ?nodeshape sh:property [ sh:path ?field ; sh:order ?ord ] .
    }
    ORDER BY ?id ?ord
"""


def nullify(field):
    if field is None:
        field = 'NULL'
    else:
        field = "'" + str(field.toPython()) + "'"
    return field


def main(shaclfile, knowledgefile, modelfile, output_folder='output'):
    yaml = ruamel.yaml.YAML()
    utils.create_output_folder(output_folder)
    with open("output/ngsild-models.sqlite", "w") as sqlitef:
        outfile = sqlitef
        g = Graph()
        g.parse(shaclfile)
        model = Graph()
        model.parse(modelfile)
        knowledge = Graph()
        knowledge.parse(knowledgefile)
        model += g + knowledge

        sh = Namespace("http://www.w3.org/ns/shacl#")
        iff = Namespace(configs.iff_namespace)


        # Create attributes table by sparql
        # query first before inferencing
        qres_noinf = model.query(ngsild_tables_query_noinference)
        # now infer types and do rest of the queries
        rdfs = owlrl.RDFSClosure.RDFS_Semantics(model, axioms=False, daxioms=False, rdfs=False).closure()
        qres = model.query(attributes_query)
        entity_count = {}
        first = True
        print(f'INSERT INTO `{configs.attributes_table_name}` VALUES', file = outfile)
        for entityId, name, type, nodeType, valueType, hasValue, hasObject in qres:
            id = entityId.toPython() + "\\\\" + name.toPython()
            if id not in entity_count:
                entity_count[id] = 0
            else:
                entity_count[id] += 1
        
            valueType = nullify(valueType)
            hasValue = nullify(hasValue)
            hasObject = nullify(hasObject)
            if "string" in valueType:
                valueType = 'NULL'
            if first:
                first = False
            else:
                print(',', file = outfile)
            print("('" + id + "', '" + entityId.toPython() + "', '" + name.toPython() +
                "', '" + nodeType + "', " + valueType + ", " + str(entity_count[id]) + 
                ", '" + type.toPython() +  "'," + hasValue  + ", " + hasObject + ", " + 'CURRENT_TIMESTAMP' +")", end = '', file = outfile)
        print(";", file = outfile)

        # Create ngsild tables by sparql
        qres = model.query(ngsild_tables_query)
        tables = {}

        # orig_class contains the real, not inferenced type, e.g. plasmacutter instead of machine, even though it is inserted in the machine table
        orig_class = {}
        for id, type, field, ord, shacltype in qres_noinf:
            if id not in orig_class:
                orig_class[id] = type
            else:
                if  (type, RDFS.subClassOf, orig_class[id]) in model:
                    orig_class[id] = type

        # Now create the entity tables 
        for id, type, field, ord in qres:
            combined_key = id.toPython() + '\\\\' + type.toPython()
            if combined_key not in tables:
                table = []
                table.append(id.toPython())
                table.append(orig_class[id])
                tables[combined_key] = table
            tables[combined_key].append(id.toPython() + "\\\\" + field.toPython())
        for id, table in tables.items():
            table.append('CURRENT_TIMESTAMP')

        for id, table in tables.items():
            type = re.search('^.*\\\\(.*)$', id)[1]
            print(f'INSERT INTO `{utils.strip_class(URIRef(type))}` VALUES', file = outfile)
            first = True
            print("(", end = '', file = outfile)
            for field in table:
                if first:
                    first = False
                else:
                    print(", ", end = '', file = outfile)
                if isinstance(field, str) and not field == 'CURRENT_TIMESTAMP':
                    print("'" + field + "'", end = '', file = outfile)
                else:
                    print(field, end = '', file = outfile)
            print(");", file = outfile)


if __name__ == '__main__':
    args = parse_args()
    shaclfile = args.shaclfile
    knowledgefile = args.knowledgefile
    modelfile = args.modelfile
    main(shaclfile, knowledgefile, modelfile)
