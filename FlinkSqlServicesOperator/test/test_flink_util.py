from unittest import TestCase
import unittest
from bunch import Bunch
from mock import patch, MagicMock
import kopf
from kopf.testing import KopfRunner

import flink_util as target
import requests


"""
Mock functions
"""

global_message = ''

class Logger():
    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def warning(self, message):
        global global_message
        global_message = message
        pass


def kopf_info(body, reason, message):
    pass


def raise_for_status_success():
    return


def raise_for_status_fail():
    raise requests.exceptions.HTTPError

def getJson():
    return "{}"

def getJsonStatus():
    return {'status': {
        'id': 'id'
        },
        'operation': {
            'location': "location"
        }
    }

def getJsonRequestId():
    requestid = Bunch()
    requestid['request-id'] = 'request-id'
    return requestid

def request_get_successful(url):
    response = Bunch()
    response.raise_for_status = raise_for_status_success
    response.json = getJson
    response.status_code = 200
    return response

def request_get_failed(url):
    response = Bunch()
    response.raise_for_status = raise_for_status_fail
    response.json = getJson
    response.status_code = 404
    return response

def request_get_successful_job_status(url):
    response = Bunch()
    response.raise_for_status = raise_for_status_success
    response.json = getJsonStatus
    response.status_code = 200
    return response

def request_post_successful(url, json):
    response = Bunch()
    response.raise_for_status = raise_for_status_success
    response.json = getJsonRequestId
    response.status_code = 202
    return response

def request_patch_successful(url):
    response = Bunch()
    response.status_code = 202
    return response

class TestJobStatus(TestCase):


    @patch('requests.get', request_get_successful)
    def test_job_status(self):
        job_id ="job_id"
        response = target.get_job_status(Logger(), job_id)
        self.assertEqual(response, "{}")
    
    @patch('requests.get', request_get_successful_job_status)
    def test_get_savepoint_state(self):
        job_id ="job_id"
        savepoint_dir = "savepoint_dir"
        response = target.get_savepoint_state(Logger(), job_id, savepoint_dir)
        self.assertEqual(response, {'status': 'id', 'location': 'location'})

    @patch('requests.patch', request_patch_successful)
    def test_cancel_job(self):
        job_id ="job_id"
        target.cancel_job(Logger(), job_id)

    @patch('requests.post', request_post_successful)
    def test_stop_job(self):
        job_id ="job_id"
        savepoint_dir = "savepoint_dir"
        response = target.stop_job(Logger(), job_id, savepoint_dir)
        self.assertEqual(response, 'request-id')

    @patch('requests.get', request_get_successful_job_status)
    def test_get_savepoint_state(self):
        job_id ="job_id"
        savepoint_dir = "savepoint_dir"
        response = target.get_savepoint_state(Logger(), job_id, savepoint_dir)
        self.assertEqual(response, {'status': 'id', 'location': 'location'})

    @patch('requests.get', request_get_failed)
    def test_get_savepoint_state_fail(self):
        job_id ="job_id"
        savepoint_dir = "savepoint_dir"
        response = target.get_savepoint_state(Logger(), job_id, savepoint_dir)
        self.assertEqual(response, {'status': 'NOT_FOUND', 'location': None})

if __name__ == '__main__':
    unittest.main()
