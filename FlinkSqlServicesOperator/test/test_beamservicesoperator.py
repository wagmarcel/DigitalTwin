from unittest import TestCase, mock
import aiounittest
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
class Logger():
    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def warning(self, message):
        pass

def getjsn():
    return {"jobs": [{"id": "id", "status": "RUNNING"}]}
def getjsnFail():
    return {"jobs": [{"id": "id", "status": "FAILED"}]}
    
def kopf_info(body, reason, message):
    pass

def check_readiness():
    return True

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


class TestUpdates(aiounittest.AsyncTestCase):
    @patch('kopf.info', kopf_info)
    async def test_update_None(self):
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
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(response, {'deployed': False, 'jobCreated': False})
        
    def delete_jar(body, jarfile):
        pass
    def deploy(body, spec, patch):
        return "deploy"

    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.delete_jar', delete_jar)
    @patch('beamservicesoperator.deploy', deploy)
    async def test_update_deployed(self):
 
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
                "job_id": "job_id",
                "updates": {},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(response, {'deployed': True, 'jarId': 'deploy'})


    def check_readiness(body):
        return 1
    def create_job(body, spec, update_status):
        return "job_id"

    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.check_readiness', check_readiness)
    @patch('beamservicesoperator.create_job', create_job)
    async def test_update_not_jobcreated(self):
 
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId"},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(response, {'jobCreated': True, 'jobId': 'job_id'})

    def check_readiness_0(body):
        return 0
    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.check_readiness', check_readiness_0)
    @patch('beamservicesoperator.create_job', create_job)
    async def test_update_not_jobcreated_not_ready(self):
 
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId"},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(response, None)

    def create_job_none(body, spec, update_status):
        return None

    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.check_readiness', check_readiness)
    @patch('beamservicesoperator.create_job', create_job_none)
    async def test_update_not_jobcreated_not_ready_no_jobid(self):
 
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId"},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(response, {'deployed': False, 'jobCreated': False})


    def requestsget(url):
        result = Bunch()
        result.json = getjsn
        return result

    @patch('kopf.info', kopf_info)
    @patch('requests.get', requestsget)
    async def test_update_not_jobcreated_not_ready_no_jobid(self):
 
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId", "jobCreated": "2345", "jobId": "id"},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(patch["status"].get("state"), "RUNNING")


    def requestsget_FAIL(url):
        result = Bunch()
        result.json = getjsnFail
        return result

    @patch('kopf.info', kopf_info)
    @patch('requests.get', requestsget_FAIL)
    async def test_update_not_jobcreated_not_ready_no_jobid_requestget_getfailed(self):
 
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId", "jobCreated": "2345", "jobId": "id"},
                "jarfile": "jarfile"
            }
        }
        patch = Bunch()
        patch.status = {}
        response = await target.updates(None, patch, Logger(), body, body["spec"], body["status"])
        self.assertEqual(patch["status"].get("state"), None)

def cancel_job(job_id):
    assert(job_id == "id")

class TestDelete(TestCase):
    @patch('kopf.info', kopf_info)
    def test_delete(self):
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
        response = target.delete(body)
        self.assertEqual(response, None)

    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.cancel_job', cancel_job)
    def test_delete_successful(self):
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
                "job_id": "job_id",
                "updates": {"deployed": "1234", "jarId": "jarId", "jobCreated": "2345", "jobId": "id"}
            }
        }
        patch = Bunch()
        patch.status = {}
        response = target.delete(body)

if __name__ == '__main__':
    unittest.main()
