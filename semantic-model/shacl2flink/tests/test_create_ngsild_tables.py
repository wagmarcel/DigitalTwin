from unittest.mock import patch, call
import create_ngsild_tables
import os


@patch('create_ngsild_tables.ruamel.yaml')
@patch('create_ngsild_tables.owlrl')
@patch('create_ngsild_tables.rdflib')
@patch('create_ngsild_tables.create_table')
@patch('create_ngsild_tables.configs')
@patch('create_ngsild_tables.utils')
def test_main(mock_utils, mock_configs, mock_create_table, mock_rdflib,
              mock_owlrl, mock_yaml, tmp_path):
    mock_configs.kafka_topic_ngsi_prefix = 'ngsild_prefix'
    mock_configs.kafka_bootstrap = 'bootstrap'
    mock_utils.create_sql_table.return_value = "sqltable"
    mock_utils.create_yaml_table.return_value = "yamltable"
    mock_utils.create_sql_view.return_value = "sqlview"
    mock_utils.create_yaml_view.return_value = "yamlview"
    mock_yaml.dump.return_value = "dump"

    create_ngsild_tables.main('kms/shacl.ttl', tmp_path)

    assert os.path.exists(os.path.join(tmp_path, 'ngsild.yaml')) is True
    assert os.path.exists(os.path.join(tmp_path, 'ngsild.sqlite')) is True
