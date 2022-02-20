/**
* Copyright (c) 2022 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/
'use strict';

const { assert } = require('chai');
const chai = require('chai');
global.should = chai.should();

const rewire = require('rewire');
const toTest = rewire('../lib/debeziumBridge.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  
describe('Test diff Attributes', function () {
    it('Should return no updates and no deletions', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var beforeAttrs = {
            "attr1": [{
                "value": "value",
                "index": 0
            }]
        }
        var afterAttrs = {
            "attr1": [{
                "value": "value",
                "index": 0
            }]
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffAttributes(beforeAttrs, afterAttrs);
        assert.deepEqual(result.updatedAttrs, {});
        assert.deepEqual(result.deletedAttrs, {});
        revert();
    });
    it('Should update value but no deletions', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var beforeAttrs = {
            "attr1": [{
                "value": "value",
                "index": 0
            }]
        }
        var afterAttrs = {
            "attr1": [{
                "value": "value2",
                "index": 0
            }]
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffAttributes(beforeAttrs, afterAttrs);
        assert.deepEqual(result.updatedAttrs, afterAttrs);
        assert.deepEqual(result.deletedAttrs, {});
        revert();
    });
    it('Should delete value but no update', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var beforeAttrs = {
            "attr1": [{
                "id": "id",
                "value": "value",
                "index": 0
            }],
            "attr2": [{
                "id": "id2",
                "value": "value3",
                "index": 0
            }]
        }
        var afterAttrs = {
            "attr1": [{
                "id": "id",
                "value": "value",
                "index": 0
            }]
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffAttributes(beforeAttrs, afterAttrs);
        assert.deepEqual(result.updatedAttrs, {});
        assert.deepEqual(result.deletedAttrs, {"attr2": [{"id":"id2", "index": 0}]});
        revert();
    });
    it('Should delete higher index value and update changed value', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var beforeAttrs = {
            "attr1": [
                {
                "id": "id",
                "value": "value",
                "index": 0
               },
               {
                "id": "id",
                "value": "value2",
                "index": 1
               }
        ],
            "attr2": [{
                "id": "id2",
                "value": "value3",
                "index": 0
            }]
        }
        var afterAttrs = {
            "attr1": [
                {
                "id": "id3",
                "value": "value4",
                "index": 0
                }
            ]
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffAttributes(beforeAttrs, afterAttrs);
        assert.deepEqual(result.updatedAttrs, {"attr1": [{"id": "id3", "value": "value4", "index": 0 }]});
        assert.deepEqual(result.deletedAttrs, {"attr2": [{"id":"id2", "index": 0}], "attr1": [{"id": "id", "index": 1}]});
        revert();
    });
});  
