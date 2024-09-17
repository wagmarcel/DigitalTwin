#
# Copyright (c) 2022 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from rdflib import Graph, URIRef
import os
import sys
import argparse
import lib.utils as utils
import lib.configs as configs
import owlrl


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='create_ngsild_models.py \
                                                  <shacl.ttl> <knowledge.ttl> \
                                                  <model.jsonld>')

    parser.add_argument('shaclfile', help='Path to the SHACL file')
    parser.add_argument('knowledgefile', help='Path to the knowledge file')
    parser.add_argument('modelfile', help='Path to the model file')
    parsed_args = parser.parse_args(args)
    return parsed_args


attributes_query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT DISTINCT (?a as ?entityId) (?b as ?name) (?e as ?type) (IF(bound(?g), IF(isIRI(?g), '@id', '@value'), IF(isIRI(?f), '@id', '@value')) as ?nodeType)
(datatype(?g) as ?valueType) (?f as ?hasValue) (?g as ?hasObject) ?observedAt ?index
where {
    ?a a ?subclass .
    {?a ?b [ ngsild:hasObject ?g ] .
    VALUES ?e {ngsild:Relationship} .
    OPTIONAl{?a ?b [ ngsild:observedAt ?observedAt; ngsild:hasObject ?g  ] .} .
    OPTIONAl{?a ?b [ ngsild:datasetId ?index; ngsild:hasObject ?g  ] .} .
    }
  UNION
  {
  	{?a ?b [ ngsild:hasValue ?f ] .
    VALUES ?e {ngsild:Property} .
    OPTIONAl{?a ?b [ ngsild:observedAt ?observedAt; ngsild:hasValue ?f  ] .} .
    OPTIONAl{?a ?b [ ngsild:datasetId ?index; ngsild:hasValue ?f  ] .} .
    }
  }
}
order by ?observedAt
"""  # noqa: E501

ngsild_tables_query_noinference = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?id ?type ?field ?tabletype
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?basetype .
    ?id a ?type .
    ?type rdfs:subClassOf* ?basetype .
    ?tabletype rdfs:subClassOf* ?basetype .
    ?type rdfs:subClassOf* ?tabletype .
    ?nodeshape sh:property [ sh:path ?field ;] .
    FILTER(?tabletype != rdfs:Resource && ?tabletype != owl:Thing && ?tabletype != owl:Nothing )
    }
    ORDER BY ?id STR(?field)
"""


def nullify(field):
    if field is None:
        field = 'NULL'
    else:
        field = "'" + str(field.toPython()) + "'"
    return field


class DatasetIndexManager:
    def __init__(self):
        # Dictionary to store (entity_id, name) -> next available number
        self.tuple_counts = {}

        # Dictionary to store the full (entity_id, name, dataset_id) -> assigned number
        self.assigned_tuples = {}

    def assign_number(self, entity_id, name, dataset_id):
        # Create a key for the full tuple
        full_key = (entity_id, name, dataset_id)
        
        # If the full tuple already exists, return the assigned number
        if full_key in self.assigned_tuples:
            return self.assigned_tuples[full_key]
        
        # Create a key based on (entity_id, name) to track the next number
        key = (entity_id, name)

        # Check if the (entity_id, name) pair already exists
        if key in self.tuple_counts:
            # Increment the number for the next dataset_id
            next_number = self.tuple_counts[key] + 1
        else:
            # If the (entity_id, name) pair does not exist, start counting from 1
            next_number = 1

        # Store the next number in the tuple_counts dictionary for the (entity_id, name) pair
        self.tuple_counts[key] = next_number
        
        # Assign this number to the full (entity_id, name, dataset_id) tuple
        self.assigned_tuples[full_key] = next_number
        
        # Return the assigned number for the tuple
        return next_number

def main(shaclfile, knowledgefile, modelfile, output_folder='output'):
    datasetIndexManager = DatasetIndexManager()
    utils.create_output_folder(output_folder)
    with open(os.path.join(output_folder, "ngsild-models.sqlite"), "w")\
            as sqlitef:
        g = Graph()
        g.parse(shaclfile)
        model = Graph()
        model.parse(modelfile)
        knowledge = Graph()
        knowledge.parse(knowledgefile)
        attributes_model = model + g + knowledge

        qres = attributes_model.query(attributes_query)
        first = True
        if len(qres) > 0:
            print(f'INSERT INTO `{configs.attributes_table_name}` VALUES',
                  file=sqlitef)
        for entityId, name, type, nodeType, valueType, hasValue, \
                hasObject, observedAt, index in qres:
            #id = entityId.toPython() + "\\\\" + name.toPython()
            current_index = None
            if index is None:
                current_index = 0
                current_dataset_id = "NULL"
            else:
                current_index = datasetIndexManager(str(entityId), str(name), str(index))
                current_dataset_id = f"'{index}'"
            valueType = nullify(valueType)
            hasValue = nullify(hasValue)
            hasObject = nullify(hasObject)
            if "string" in valueType:
                valueType = 'NULL'
            if first:
                first = False
            else:
                print(',', file=sqlitef)
            current_timestamp = "CURRENT_TIMESTAMP"
            if observedAt is not None:
                current_timestamp = f"'{str(observedAt)}'"
            print("('" + entityId.toPython() + "', '" +
                  name.toPython() +
                  "', '" + nodeType + "', " + valueType + ", '" + type.toPython() + "', " + str(current_dataset_id) +
                  "," + hasValue + ", " +
                  hasObject + ", " + current_timestamp + ")", end='',
                  file=sqlitef)
        print(";", file=sqlitef)

        # Create ngsild tables by sparql
        owlrl.DeductiveClosure(owlrl.OWLRL_Extension, rdfs_closure=True, axiomatic_triples=True,
                               datatype_axioms=True).expand(knowledge)
        table_model = model + knowledge + g
        qres = table_model.query(ngsild_tables_query_noinference)
        tables = {}

        # Now create the entity tables
        for id, type, field, tabletype in qres:
            key = utils.camelcase_to_snake_case(utils.strip_class(tabletype.toPython()))
            if key not in tables:
                table = {}

                tables[key] = table
            idstr = id.toPython()
            if idstr not in tables[key]:
                tables[key][idstr] = []
                tables[key][idstr].append(idstr)
                tables[key][idstr].append(type.toPython())
                tables[key][idstr].append('CURRENT_TIMESTAMP')
        #    tables[key][idstr].append(idstr + "\\\\" +
        #                              field.toPython())
        for type, ids in tables.items():
            for id, table in ids.items():
                print(f'INSERT INTO `entity` VALUES',
                      file=sqlitef)
                first = True
                print("(", end='', file=sqlitef)
                for field in table:
                    if first:
                        first = False
                    else:
                        print(", ", end='', file=sqlitef)
                    if isinstance(field, str) and not field ==\
                            'CURRENT_TIMESTAMP':
                        print("'" + field + "'", end='', file=sqlitef)
                    else:
                        print(field, end='', file=sqlitef)
                print(");", file=sqlitef)


if __name__ == '__main__':
    args = parse_args()
    shaclfile = args.shaclfile
    knowledgefile = args.knowledgefile
    modelfile = args.modelfile
    main(shaclfile, knowledgefile, modelfile)
