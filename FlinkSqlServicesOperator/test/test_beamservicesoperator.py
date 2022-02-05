from unittest import TestCase, mock
import aiounittest
import unittest
from urllib import response
from bunch import Bunch
from mock import patch, mock_open
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
def getjsonPost():
    return {"filename": "/filename"}
def getjsonPut():
    return {"name": "name"}

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


    def requestsget_good(url):
        result = Bunch()
        try:
            url.index("/jobs/")
        except ValueError:
            result.json = getjsn
        else:
            result.json = getjsonPut
        return result

    def get_jobname_prefix(body, spec):
        return "nam"


    def cancel_job(job_id):
        pass
    @patch('kopf.info', kopf_info)
    @patch('requests.get', requestsget_good)
    @patch('beamservicesoperator.get_jobname_prefix', get_jobname_prefix)
    @patch('beamservicesoperator.cancel_job', cancel_job)
    async def test_update_not_jobcreated_not_ready_not_matching_joid(self):
 
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
                "updates": {"deployed": "1234", "jarId": "jarId", "jobCreated": "2345", "jobId": "otherid"},
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
        self.assertEqual(response, None)

class TestHelpers(TestCase):
    def requestget(url):
        assert(url == 'url')
        result = Bunch()
        result.content = b'content'
        return result
    
    def download_file_via_ftp(url, username, password):
        return "jarfilepath"

    @patch('requests.get', requestget)
    def test_download_file_http(self):
        m = mock_open()
        with patch('__main__.open', m, create=True):
            with open('foo', 'wb') as h:
                h.write(b'some stuff')
        response = target.download_file_via_http('url')
        self.assertRegex(response, r"/tmp/[a-f0-9-]*\.jar") 

    @patch('ftplib.FTP', autospec=True)
    def test_download_file_ftp(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        m = mock_open()
        with patch('__main__.open', m, create=True):
            with open('foo', 'wb') as h:
                h.write(b'some stuff')
        response = target.download_file_via_ftp('ftp://url', 'username', 'password')
        mock_ftp_constructor.assert_called_with('url', 'username', 'password')
        self.assertRegex(response, r"/tmp/[a-f0-9-]*\.jar")

    def requestpost(url, files):
        response = Bunch()
        response.status_code = 200
        response.json = getjsonPost
        return response

    @patch('requests.post', requestpost)
    @patch('kopf.info', kopf_info)
    @patch('beamservicesoperator.download_file_via_ftp', download_file_via_ftp)
    def test_deploy_ftp(self):
        
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                'package': {
                    'url': 'ftp://url',
                    'username': 'username',
                    'password': 'password' 
                }
            },
            "status": {
            }
        }
        patchx = Bunch()
        patchx.status = {}
        m = mock_open(read_data='data')
        with mock.patch('builtins.open', m, create=True):
            with open('jarfilepath') as h:
                response = target.deploy(body, body["spec"], patchx)
        self.assertEqual(response, "filename")

    def util_format_template(string, tokens, encode):
        return "format"

    @patch('util.format_template', util_format_template)
    def test_build_args(self):
        
        args_dict = {
           "key1": "value1",
           "key2": "value2",
           "config": {
               "format": "value"
           }
        }
        tokens = {
            "key": "value"
        }
        response = target.build_args(args_dict, tokens)
        self.assertEqual(response, '--key1=value1 --key2=value2 --config=format ')

    @patch('kopf.info', kopf_info)
    @patch('util.format_template', util_format_template)
    def test_get_jobname_prefix(self):
        
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "entryClass": "org.entryClass"
            },
            "status": {
            }
        }
        response = target.get_jobname_prefix(body, body["spec"])
        self.assertEqual(response, 'entryclass')

    that = None
    def get_tokens(users):
        that.assertDictEqual(users[0], {"user": "user", "password": "password"})
        return {"user1": "token1", "user2": "token2"}
    def build_args(args_dict, tokens):
        that.assertDictEqual(args_dict, {"runner": "runner"})
        that.assertDictEqual(tokens, {"user1": "token1", "user2": "token2"})
        pass

    def request_post_run(url, json):
        def json_run():
            return {"jobid": "jobid"}
        result = Bunch()
        result.status_code = 200
        result.json = json_run
        return result
    @patch('kopf.info', kopf_info)
    @patch('requests.post', request_post_run)
    @patch('util.get_tokens', get_tokens)
    @patch('beamservicesoperator.build_args', build_args)
    def test_create_job(self):
        global that
        that = self
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "entryClass": "org.entryClass",
                "tokens": [
                    {
                        "user": "user",
                        "password": "password"
                    }
                ],
                "args": {"runner": "runner"}
            },
            "status": {
            }
        }
        response = target.create_job(body, body['spec'], 'jar_id')
        self.assertEqual(response, 'jobid')

if __name__ == '__main__':
    unittest.main()
