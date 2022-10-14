from click import UsageError
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
import os
import sys
import lib.configs as configs
from urllib.parse import urlparse
import ruamel.yaml
import lib.utils as utils
from ruamel.yaml.scalarstring import (DoubleQuotedScalarString as dq, 
                                      SingleQuotedScalarString as sq)
yaml = ruamel.yaml.YAML()


def main():
    utils.create_output_folder()

    kafka_topic_bulk_alerts = configs.kafka_topic_bulk_alerts
    kafka_topic_listen_alerts = configs.kafka_topic_listen_alerts
    kafka_topic_ngsild_updates = configs.kafka_topic_ngsild_updates
    kafka_topic_attributes = configs.kafka_topic_attributes
    kafka_bootstrap = configs.kafka_bootstrap

    f = open("output/core.yaml", "w")
    sqlitef = open("output/core.sqlite", "w")

    #g = Graph()
    #g.parse(allFile)
    sh = Namespace("http://www.w3.org/ns/shacl#")
    tables = {}
    sqllite = ''


    # alerts table
    table_name = "alerts"
    connector = 'upsert-kafka'
    table = [{'resource': 'STRING'},
             {'event': 'STRING'},
             {'environment': 'STRING'},
             {'service': 'ARRAY<STRING>'},
             {'severity': 'STRING'},
             {'customer': 'STRING'},
             {'text': 'STRING'}]
    table_sqlite = [{'resource': 'STRING'},
             {'event': 'STRING'},
             {'environment': 'STRING'},
             {'service': 'STRING'},
             {'severity': 'STRING'},
             {'customer': 'STRING'},
             {'text': 'STRING'}]
    primary_key = ['resource', 'event']
    kafka = {'topic': kafka_topic_listen_alerts, 
             'properties': {'bootstrap.servers': kafka_bootstrap},
             'key.format': 'json'
            }
    value = {
                'format': 'json',
                'json.fail-on-missing-field': False,
                'json.ignore-parse-errors': True
            }

    print('---', file=f)
    yaml.dump(utils.create_yaml_table(table_name, connector, table, primary_key, kafka, value), f)
    print(utils.create_sql_table(table_name, table_sqlite, primary_key), file=sqlitef)

    # alerts-bulk table
    table_name = "alerts-bulk"
    spec_name = "alerts_bulk"
    connector = 'upsert-kafka'
    table = [{'resource': 'STRING'},
             {'event': 'STRING'},
             {'environment': 'STRING'},
             {'service': 'ARRAY<STRING>'},
             {'severity': 'STRING'},
             {'customer': 'STRING'},
             {'text': 'STRING'},
             {'watermark': 'FOR `ts` AS `ts`'},
             {'ts': ' TIMESTAMP(3) METADATA VIRTUAL'}]
    table_sqlite = [{'resource': 'STRING'},
             {'event': 'STRING'},
             {'environment': 'STRING'},
             {'service': 'STRING'},
             {'severity': 'STRING'},
             {'customer': 'STRING'},
             {'text': 'STRING'},
             {'watermark': 'FOR `ts` AS `ts`'},
             {'ts': ' TIMESTAMP(3) METADATA VIRTUAL'}]
    primary_key = ['resource', 'event']
    kafka = {'topic': kafka_topic_bulk_alerts, 
             'properties': {'bootstrap.servers': kafka_bootstrap},
             'key.format': 'json'
            }
    value = {
                'format': 'json',
                'json.fail-on-missing-field': False,
                'json.ignore-parse-errors': True
            }

    print('---', file=f)
    yaml.dump(utils.create_yaml_table(spec_name, connector, table, primary_key, kafka, value), f)
    print(utils.create_sql_table(spec_name, table_sqlite, primary_key, utils.SQL_DIALECT.SQLITE), file=sqlitef)
    print(utils.create_sql_view(spec_name, table_sqlite, primary_key, []), file=sqlitef)

    # ngsild-updates table
    table_name = "ngsild-updates"
    spec_name = "ngsild_updates"
    connector = 'kafka'
    table = [{'op': 'STRING'},
             {'overwirteOrReplace': 'BOOLEAN'},
             {'noForward': 'BOOLEAN'},
             {'entities': 'STRING'}]
    primary_key = None
    kafka = {'topic': kafka_topic_ngsild_updates, 
             'properties': {'bootstrap.servers': kafka_bootstrap},
             'scan.startup.mode': 'latest-offset'
            }
    value = {
                'format': 'json',
                'json.fail-on-missing-field': False,
                'json.ignore-parse-errors': True
            }

    print('---', file=f)
    yaml.dump(utils.create_yaml_table(spec_name, connector, table, primary_key, kafka, value), f)
    print(utils.create_sql_table(spec_name, table, primary_key), file=sqlitef)

    # attributes table
    table_name = "attributes"
    spec_name = "attributes"
    connector = 'kafka'
    table = [{'id': 'STRING'},
             {'entityId': 'STRING'},
             {'name': 'STRING'},
             {'nodeType': 'STRING'},
             {'valueType': 'STRING'},
             {'index': 'INTEGER'},
             {'type': 'STRING'},
             {'https://uri.etsi.org/ngsi-ld/hasValue': 'STRING'},
             {'https://uri.etsi.org/ngsi-ld/hasObject': 'STRING'},
             {'watermark': 'FOR `ts` AS `ts`'},
             {'ts': "TIMESTAMP(3) METADATA FROM 'timestamp'"}]
    primary_key = None
    kafka = {'topic': kafka_topic_attributes, 
             'properties': {'bootstrap.servers': kafka_bootstrap},
             'scan.startup.mode': 'earliest-offset'
            }
    value = {
                'format': 'json',
                'json.fail-on-missing-field': False,
                'json.ignore-parse-errors': True
            }

    print('---', file=f)
    yaml.dump(utils.create_yaml_table(table_name, connector, table, primary_key, kafka, value), f)
    print(utils.create_sql_table(table_name, table, primary_key, utils.SQL_DIALECT.SQLITE), file=sqlitef)
    print('---', file=f)
    yaml.dump(utils.create_yaml_view(table_name, table, ['id', 'index']), f)
    print(utils.create_sql_view(table_name, table, ['id', 'index']), file=sqlitef)

if __name__ == '__main__':
    main()
