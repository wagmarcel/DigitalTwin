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

from rdflib import Graph
from rdflib.namespace import OWL
import os
import sys
import argparse
import ruamel.yaml
import lib.utils as utils
import lib.configs as configs
from ruamel.yaml.scalarstring import (SingleQuotedScalarString as sq)
import owlrl


field_query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT DISTINCT ?path ?shacltype
where {
  {    ?nodeshape a sh:NodeShape .
      ?nodeshape sh:targetClass ?shacltypex .
      ?shacltype rdfs:subClassOf* ?shacltypex .
      ?nodeshape sh:property [ sh:path ?path ; ] .

  }
    UNION
  {    ?nodeshape a sh:NodeShape .
      ?nodeshape sh:targetClass ?shacltypex .
      ?shacltype rdfs:subClassOf* ?shacltypex .
      FILTER NOT EXISTS {
          ?nodeshape sh:property [ sh:path ?path ; ] .
      }
    BIND(owl:Nothing as ?path)
  }
}
    ORDER BY STR(?path)
"""


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='create_ngsild_tables.py')
    #parser.add_argument('shaclfile', help='Path to the SHACL file')
    #parser.add_argument('knowledgefile', help='Path to the Knowledge file')
    parsed_args = parser.parse_args(args)
    return parsed_args


def main(output_folder='output'):
    yaml = ruamel.yaml.YAML()
    utils.create_output_folder(output_folder)


    # Kafka topic object for RDF
    config = {}
    config['retention.ms'] = configs.kafka_topic_ngsi_retention
    with open(os.path.join(output_folder, "ngsild.yaml"), "w") as f, \
            open(os.path.join(output_folder, "ngsild.sqlite"), "w") as sqlitef, \
            open(os.path.join(output_folder, "ngsild-kafka.yaml"), "w") as fk:

        # Create "entity"
        value = {
                'format': 'json',
                'json.fail-on-missing-field': False,
                'json.ignore-parse-errors': True
        }
        connector = 'kafka'
        base_entity_table = []
        base_entity_table.append({sq("id"): "STRING"})
        base_entity_table.append({sq("type"): "STRING"})
        base_entity_table.append({sq("ts"): "TIMESTAMP(3) METADATA FROM 'timestamp'"})
        base_entity_table.append({"watermark": "FOR `ts` AS `ts`"})

        base_entity_tablename = configs.kafka_topic_ngsi_prefix_name
        base_entity_primary_key = None
        print('---', file=f)
        yaml.dump(utils.create_yaml_table(base_entity_tablename, connector,  base_entity_table,
                                              base_entity_primary_key, "relationshipChecksTable", value), f)
        print(utils.create_sql_table(base_entity_tablename, base_entity_table, base_entity_primary_key,
                                    utils.SQL_DIALECT.SQLITE),
        file=sqlitef)
        print('---', file=f)
        base_entity_view_primary_key = ['id']
        yaml.dump(utils.create_yaml_view(base_entity_tablename, base_entity_table, base_entity_view_primary_key), f)
        print(utils.create_sql_view(base_entity_tablename, base_entity_table, base_entity_view_primary_key), file=sqlitef)
        print('---', file=fk)
        yaml.dump(utils.create_kafka_topic(f'{configs.kafka_topic_ngsi_prefix}',
                                               f'{configs.kafka_topic_ngsi_prefix}', configs.kafka_topic_object_label,
                                               config), fk)
        # Create property_checks and relational_checks
        print('---', file=f)
        yaml.dump(utils. create_relationship_check_yaml_table(connector, value), f)
        print('---', file=f)
        yaml.dump(utils.create_property_check_yaml_table(connector, value), f)
        print(utils.create_relationship_check_sql_table(),
              file=sqlitef)
        print(utils.create_property_check_sql_table(),
              file=sqlitef)
if __name__ == '__main__':
    args = parse_args()
    main()
