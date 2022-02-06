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
from unittest import TestCase
import unittest
from bunch import Bunch
from mock import patch
import kopf
import requests

import beamsqlstatementsetoperator as target


# Mock functions
# --------------

class Logger():
    """
    mock for Logger
    """
    def info(self, message):
        """
        mock for info
        """

    def debug(self, message):
        """
        mock for debug
        """

    def error(self, message):
        """
        mock for error
        """

    def warning(self, message):
        """
        mock for warnings
        """

# pylint: disable=unused-argument
def kopf_info(body, reason, message):
    """
    mock for kopf.info
    """

def check_readiness():
    """mock for check_rediness - successful"""
    return True

class TestInit(TestCase):
    """unit test class for kopf init"""
    @patch('kopf.info', kopf_info)
    def test_init(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {}
        }
        patch = Bunch()
        patch.status = {}
        result = target.create(body, body["spec"], patch, Logger())
        self.assertIsNotNone(result['createdOn'])
        self.assertEqual(patch.status['state'], "INITIALIZED")
        self.assertIsNone(patch.status['job_id'])


class TestMonitoring(TestCase):
    def create_ddl_from_beamsqltables(beamsqltable, logger):
        return "DDL;"

    def submit_statementset_successful(statementset, logger):
        # Keeping normal assert statement as this does not seem to
        # be an object method after mocking
        assert statementset == "SET pipeline.name = 'namespace/name';\nDDL;" \
            "\nBEGIN STATEMENT SET;\nselect;\nEND;"
        return "job_id"

    def submit_statementset_failed(statementset, logger):
        raise target.DeploymentFailedException("Mock submission failed")

    def update_status_not_found(body, patch, logger):
        patch.status["state"] = "NOT_FOUND"

    @patch('beamsqlstatementsetoperator.tables_and_views.create_ddl_from_beamsqltables',
           create_ddl_from_beamsqltables)
    @patch('beamsqlstatementsetoperator.deploy_statementset',
           submit_statementset_successful)
    def test_update_submission(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "INITIALIZED",
                "job_id": None
            }
        }

        patch = Bunch()
        patch.status = {}

        beamsqltables = {("namespace", "table"): ({}, {})}
        target.monitor(beamsqltables, None, patch,  Logger(),
                       body, body["spec"], body["status"])
        self.assertEqual(patch.status['state'], "DEPLOYING")
        self.assertEqual(patch.status['job_id'], "job_id")

    @patch('beamsqlstatementsetoperator.tables_and_views.create_ddl_from_beamsqltables',
           create_ddl_from_beamsqltables)
    @patch('beamsqlstatementsetoperator.deploy_statementset',
           submit_statementset_failed)
    def test_update_submission_failure(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "INITIALIZED",
                "job_id": None
            }
        }

        patch = Bunch()
        patch.status = {}

        beamsqltables = {("namespace", "table"): ({}, {})}
        try:
            target.monitor(beamsqltables, None, patch,  Logger(),
                           body, body["spec"], body["status"])
        except kopf.TemporaryError:
            pass
        self.assertEqual(patch.status['state'], "DEPLOYMENT_FAILURE")
        self.assertIsNone(patch.status['job_id'])

    @patch('beamsqlstatementsetoperator.tables_and_views.create_ddl_from_beamsqltables',
           create_ddl_from_beamsqltables)
    @patch('beamsqlstatementsetoperator.deploy_statementset',
           submit_statementset_failed)
    def test_update_table_failure(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "INITIALIZED",
                "job_id": None
            }
        }

        patch = Bunch()
        patch.status = {}

        beamsqltables = {}
        with self.assertRaises(kopf.TemporaryError) as cm:
            target.monitor(beamsqltables, None, patch, Logger(),
                           body, body["spec"], body["status"])
            self.assertTrue(str(cm.exception).startswith(
                "Table DDLs could not be created for namespace/name."))

    @patch('beamsqlstatementsetoperator.tables_and_views.create_ddl_from_beamsqltables',
           create_ddl_from_beamsqltables)
    @patch('beamsqlstatementsetoperator.deploy_statementset',
           submit_statementset_failed)
    @patch('beamsqlstatementsetoperator.refresh_state', update_status_not_found)
    def test_update_handle_unknown(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "RUNNING",
                "job_id": "job_id"
            }
        }

        patch = Bunch()
        patch.status = {}

        beamsqltables = {}

        target.monitor(beamsqltables, None, patch, Logger(),
                       body, body["spec"], body["status"])
        self.assertEqual(patch.status["state"], "INITIALIZED")
        self.assertIsNone(patch.status["job_id"])

    def create_sets(spec, body, namespace, name, logger):
        return "sets"

    def create_tables(beamsqltables, spec, body, namespace, name, logger):
        return "tables"

    @patch('beamsqlstatementsetoperator.create_sets', create_sets)
    @patch('beamsqlstatementsetoperator.create_tables', create_tables)
    def test_update_handle_views(self):
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

        beamsqltables = {}
        beamsqlviews = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "sqlstatement": "sqlstatement"
        }
        with self.assertRaises(kopf.TemporaryError) as cm:
            target.monitor(beamsqltables, None, patch, Logger(),
                       body, body["spec"], body["status"])

class TestDeletion(TestCase):
    def update_status_nochange(body, patch, logger):
        pass

    def update_status_change(body, patch, logger):
        patch.status["state"] = "CANCELED"

    def cancel_job(logger, job_id):
        pass

    def cancel_job_error(logger, job_id):
        raise kopf.TemporaryError("Could not cancel job")

    @patch('kopf.info', kopf_info)
    def test_canceled_delete(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "CANCELED",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {}

        target.delete(body, body["spec"], patch, Logger())
        self.assertEqual(patch.status, {})

    @patch('kopf.info', kopf_info)
    @patch('beamsqlstatementsetoperator.refresh_state', update_status_nochange)
    def test_canceling_delete(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "CANCELING",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {"state": ""}

        with self.assertRaises(kopf.TemporaryError) as cm:
            target.delete(body, body["spec"], patch, Logger())
            self.assertTrue(str(cm.exception).startswith("Cancelling,"))

    @patch('kopf.info', kopf_info)
    @patch('beamsqlstatementsetoperator.refresh_state', update_status_change)
    def test_canceling_delete(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "CANCELING",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {"state": ""}

        target.delete(body, body["spec"], patch, Logger())

    @patch('flink_util.cancel_job', cancel_job)
    @patch('beamsqlstatementsetoperator.refresh_state', update_status_nochange)
    @patch('kopf.info', kopf_info)
    def test_canceling_delete_flink_ok(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "RUNNING",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {"state": ""}

        with self.assertRaises(kopf.TemporaryError) as cm:
            target.delete(body, body["spec"], patch, Logger())
            self.assertTrue(str(cm.exception).startswith("Waiting for"))
        self.assertEqual(patch.status["state"], "CANCELING")

    @patch('flink_util.cancel_job', cancel_job_error)
    @patch('kopf.info', kopf_info)
    def test_canceling_delete_flink_error(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "sqlstatements": ["select;"],
                "tables": ["table"]
            },
            "status": {
                "state": "RUNNING",
                "job_id": "job_id"
            }
        }
        patch = Bunch()
        patch.status = {"state": ""}

        with self.assertRaises(kopf.TemporaryError) as cm:
            target.delete(body, body["spec"], patch, Logger())
            self.assertTrue(str(cm.exception).startswith("Error trying"))
        self.assertNotEqual(patch.status["state"], "CANCELING")

job_canceled = False

class TestUpdate(TestCase):
    def cancel_job(logger, job_id):
        global job_canceled
        job_canceled = True
        pass
    def get_job_status(logger, job_id):
        return {
            "state": "RUNNING"
        }

    def get_job_status_not_running(logger, job_id):
        return {
            "state": "UNKNOWN"
        }

    def cancel_job_and_get_state(logger, body, patch):
        pass

    def cancel_job_and_get_state_fail(logger, body, patch):
        raise requests.exceptions.RequestException("Error")

    def stop_job(logger, job_id, savepoint_dir):
        return "savepoint_id"


    def get_savepoint_state_successful(logger, job_id, savepoint_id):
        return {
            "status": "SUCCESSFUL",
            "location": "location"
        }


    def get_savepoint_state_in_progress(logger, job_id, savepoint_id):
        return {
            "status": "IN_PROGRESS",
            "location": "location"
        }


    def get_savepoint_state_not_found(logger, job_id, savepoint_id):
        return {
            "status": "NOT_FOUND",
            "location": "location"
        }

    def add_message(logger, body, patch, reason, mtype):
        pass

    @patch('kopf.info', kopf_info)
    @patch('flink_util.cancel_job', cancel_job)
    @patch('flink_util.get_job_status', get_job_status)
    def test_cancel_job_and_get_state_running(self):
        global job_canceled
        body = {
            "status": {
                "job_id": "job_id"
            }
        }
        job_canceled = False
        job_state = target.cancel_job_and_get_state(Logger(), body, None)
        self.assertEqual("RUNNING", job_state)
        self.assertEqual(True, job_canceled)




    @patch('kopf.info', kopf_info)
    @patch('flink_util.cancel_job', cancel_job)
    @patch('flink_util.get_job_status', get_job_status_not_running)
    def test_cancel_job_and_get_state_not_running(self):
        global job_canceled
        body = {
            "status": {
                "job_id": "job_id"
            }
        }
        job_canceled = False
        job_state = target.cancel_job_and_get_state(Logger(), body, None)
        self.assertEqual("UNKNOWN", job_state)
        self.assertEqual(False, job_canceled)


    @patch('kopf.info', kopf_info)
    @patch('beamsqlstatementsetoperator.cancel_job_and_get_state', cancel_job_and_get_state)
    def test_update_no_savepoint(self):
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patch = Bunch()
        patch.status = {}
        target.update(body, body["spec"], patch, Logger())
        self.assertEqual(patch.status["state"], "UPDATING")
        self.assertIsNone(patch.status["savepoint_id"])
        self.assertIsNone(patch.status["location"])


    @patch('kopf.info', kopf_info)
    @patch('beamsqlstatementsetoperator.cancel_job_and_get_state', cancel_job_and_get_state)
    def test_update_none_savepoint(self):
        """test update without savepoint successful"""
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "updateStrategy": None
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patchx = Bunch()
        patchx.status = {}
        target.update(body, body["spec"], patchx, Logger())
        self.assertEqual(patchx.status["state"], "UPDATING")
        self.assertIsNone(patchx.status["savepoint_id"])
        self.assertIsNone(patchx.status["location"])

    @patch('kopf.info', kopf_info)
    @patch('beamsqlstatementsetoperator.cancel_job_and_get_state', cancel_job_and_get_state_fail)
    def test_update_none_savepoint(self):
        """test update without savepoint fail"""
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "updateStrategy": None
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patchx = Bunch()
        patchx.status = {}
        with self.assertRaises(kopf.TemporaryError):
            target.update(body, body["spec"], patchx, Logger())

    @patch('kopf.info', kopf_info)
    @patch('flink_util.stop_job', stop_job)
    @patch('flink_util.get_savepoint_state', get_savepoint_state_successful)
    @patch('beamsqlstatementsetoperator.add_message', add_message)
    def test_update_savepoint_successful(self):
        """test update_savepoint successful"""
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "updateStrategy": "savepoint"
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patchx = Bunch()
        patchx.status = {}
        target.update(body, body["spec"], patchx, Logger())
        self.assertEqual(patchx.status["savepoint_id"], "savepoint_id")
        self.assertEqual(patchx.status["state"], "UPDATING")
        self.assertEqual(patchx.status["location"], "location")


    @patch('kopf.info', kopf_info)
    @patch('flink_util.stop_job', stop_job)
    @patch('flink_util.get_savepoint_state', get_savepoint_state_in_progress)
    @patch('beamsqlstatementsetoperator.add_message', add_message)
    def test_update_savepoint_in_progress(self):
        """test update_savepoint when savepointing is in progress"""
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "updateStrategy": "savepoint"
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patchx = Bunch()
        patchx.status = {}
        with self.assertRaises(kopf.TemporaryError):
            target.update(body, body["spec"], patchx, Logger())
        self.assertEqual(patchx.status["savepoint_id"], "savepoint_id")
        self.assertEqual(patchx.status["state"], "SAVEPOINTING")


    @patch('kopf.info', kopf_info)
    @patch('flink_util.stop_job', stop_job)
    @patch('flink_util.get_savepoint_state', get_savepoint_state_not_found)
    @patch('beamsqlstatementsetoperator.add_message', add_message)
    def test_update_savepoint_not_found(self):
        """test savepoint update strategy where savepoint not found"""
        body = {
            "metadata": {
                "name": "name",
                "namespace": "namespace"
            },
            "spec": {
                "updateStrategy": "savepoint"
            },
            "status": {
                "job_id": "job_id",
                "state": "RUNNING",
            }
        }
        patchx = Bunch()
        patchx.status = {}
        target.update(body, body["spec"], patchx, Logger())
        self.assertIsNone(patchx.status["savepoint_id"])
        self.assertEqual(patchx.status["state"], "RUNNING")
        self.assertIsNone(patchx.status["location"])

class TestHelpers(TestCase):
    """unit test class for helpers"""
    # pylint: disable=no-self-use, no-self-argument
    def send_successful(test, json):
        """mock send job successful"""
        def jsonp():
            jsonres = Bunch()
            jsonres.job_id = "jobid"
            return jsonres
        response = Bunch()
        response.status_code = 200
        response.json = jsonp
        return response

    # pylint: disable=no-self-use, no-self-argument
    def send_unsuccessful(test, json):
        """mock send job unsuccessful"""
        def jsonp():
            jsonres = Bunch()
            jsonres.job_id = "jobid"
            return jsonres
        response = Bunch()
        response.status_code = 400
        response.json = jsonp
        return response

    # pylint: disable=no-self-use, no-self-argument
    def get_job_status(logger, jobid):
        """mock get job status"""
        return {
            "state": "ok"
        }
    # pylint: disable=no-self-use, no-self-argument
    def get_job_status_none(logger, jobid):
        """mock no job_status found"""
        return None

    # pylint: disable=no-self-use, no-self-argument
    def send_exception(test, json):
        """mock send_exception"""
        raise requests.RequestException("Error")

    @patch('kopf.info', kopf_info)
    @patch('requests.post', send_successful)
    # pylint: disable=no-self-use
    def test_deploy_statementset(self):
        """test deploy_statementset successful"""
        statementset = 'statementset'
        target.deploy_statementset(statementset, Logger())

    @patch('kopf.info', kopf_info)
    @patch('requests.post', send_unsuccessful)
    def test_deploy_statementset_unsuccessful(self):
        """test deploy_statementset unsuccessful"""
        statementset = 'statementset'
        with self.assertRaises(target.DeploymentFailedException):
            target.deploy_statementset(statementset, Logger())

    @patch('kopf.info', kopf_info)
    @patch('requests.post', send_exception)
    def test_deploy_statementset_exception(self):
        """test deploy_stamenetset with exception"""
        statementset = 'statementset'
        with self.assertRaises(target.DeploymentFailedException):
            target.deploy_statementset(statementset, Logger())

    def test_add_message(self):
        """test add_message with string message"""
        reason = 'reason'
        body = Bunch()
        body.status = Bunch()
        body.status.messages = []
        mtype = 'mtype'
        patchx = Bunch()
        patchx.status = {}
        target.add_message(Logger(), body, patchx, reason, mtype)
        self.assertEqual(patchx.status.get('messages')[0].get('message'), reason)

    def test_add_message_none(self):
        """"test add_message with None"""
        reason = 'reason'
        body = Bunch()
        body.status = Bunch()
        mtype = 'mtype'
        patchx = Bunch()
        patchx.status = {}
        target.add_message(Logger(), body, patchx, reason, mtype)
        self.assertEqual(patchx.status.get('messages')[0].get('message'), reason)

    @patch('flink_util.get_job_status', get_job_status)
    def test_get_job_state(self):
        """test get_job_state"""
        body = Bunch()
        body.status = {
            "job_id": "job_id"
        }
        job_state = target.get_job_state(Logger(), body)
        self.assertEqual(job_state, "ok")

    @patch('flink_util.get_job_status', get_job_status)
    def test_refresh_state(self):
        """test refresh_state"""
        body = Bunch()
        patchx = Bunch()
        patchx.status = {}
        body.status = { "job_id": "job_id" }

        target.refresh_state(body, patchx, Logger())
        self.assertEqual("ok", patchx.status.get('state'))
    @patch('flink_util.get_job_status', get_job_status_none)
    def test_refresh_state_none(self):
        """test refresh_state with return None"""
        body = Bunch()
        patchx = Bunch()
        patchx.status = {}
        body.status = { "job_id": "job_id" }

        target.refresh_state(body, patchx, Logger())
        self.assertEqual("UNKNOWN", patchx.status.get('state'))
if __name__ == '__main__':
    unittest.main()
