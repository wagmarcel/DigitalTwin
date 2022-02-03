from unittest import TestCase
import unittest
from bunch import Bunch
from mock import patch, MagicMock
import kopf
from kopf.testing import KopfRunner

import util as target
import requests


"""
Mock functions
"""

get_environ_ENV = {
    "conf": '{ "a": "b"}'
}

def oisp_token():
    value = Bunch()
    value.value = "token"
    return value

def auth_pass(user, password):
    pass

def oisp_pass(url):
    client = Bunch()
    client.auth = auth_pass
    client.get_user_token = oisp_token
    return client

class TestUtils(TestCase):
    
    @patch('os.environ', get_environ_ENV)
    def test_load_config(self):
        response = target.load_config_from_env("conf")
        self.assertEqual(response, {"a": "b"})

    @patch('oisp.Client', oisp_pass)
    #@patch('oisp.auth', oisp_token)
    def test_get_tokens(self):
        response = target.get_tokens([{"user" : "username", "password": "password"}])
        self.assertEqual(response, {"username": "token"})
if __name__ == '__main__':
    unittest.main()
