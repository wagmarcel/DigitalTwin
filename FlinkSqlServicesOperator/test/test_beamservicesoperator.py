from unittest import TestCase, mock
import unittest
from urllib import response
from bunch import Bunch
from mock import patch, MagicMock
import kopf
from kopf.testing import KopfRunner
import os

import beamservicesoperator as target


"""
Mock functions
"""

def kopf_info(body, reason, message):
    pass


class TestCreate(TestCase):
    @patch('kopf.info', kopf_info)
    def test_create(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"],
                "views": ["view"]
            },
            "status": {
                "state": "INITIALIZED",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = target.create(body, body["spec"], patch)
        self.assertTrue(response.get("createdOn"))

if __name__ == '__main__':
    unittest.main()
