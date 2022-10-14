import os.path
from unittest.mock import patch, call
import create_core_tables
import builtins


@patch('create_rdf_table.ruamel.yaml')
@patch('create_rdf_table.owlrl')
@patch('create_rdf_table.rdflib')
@patch('create_rdf_table.create_table')
@patch('create_rdf_table.configs')
@patch('create_rdf_table.utils')
def test_main(mock_utils, mock_configs, mock_create_table, mock_rdflib,
              mock_owlrl, mock_yaml):
    mock_configs.kafka_topic_bulk_alerts = 'bulk_alerts'
    mock_configs.kafa_topic_listen_alerts = 'listen_alerts'
    mock_configs.kafka_topic_ngsild_updates = 'ngsild_updates'
    mock_configs.kafka_topic_attributes = 'attributes'
    mock_configs.kafka_bootstrap = 'bootstrap'
    mock_utils.create_sql_table.return_value = "sqltable"
    mock_utils.create_yaml_table.return_value = "yamltable"
    mock_utils.create_sql_view.return_value = "sqlview"
    mock_utils.create_yaml_view.return_value = "yamlview"
    mock_yaml.dump.return_value = "dump"


    with patch('builtins.open') as mocked_open:
        create_core_tables.main()

        mocked_open.assert_has_calls([call("output/core.yaml", "w"), 
                                      call("output/core.sqlite", 'w')])
