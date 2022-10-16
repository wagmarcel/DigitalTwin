from unittest.mock import patch
import os

import create_sql_checks_from_shacl


@patch('create_sql_checks_from_shacl.ruamel.yaml')
@patch('create_sql_checks_from_shacl.utils')
def test_main(mock_utils, mock_yaml, tmp_path):
    def __add__(self, other):
        return self

    mock_utils.create_statementset.return_value = 'create_statementsets'

    create_sql_checks_from_shacl.main('kms/shacl.ttl', 'kms/knowledge.ttl',
                                      tmp_path)
    assert os.path.exists(os.path.join(tmp_path, 'shacl-validation.sqlite'))\
        is True
    assert os.path.exists(os.path.join(tmp_path, 'shacl-validation.yaml'))\
        is True
