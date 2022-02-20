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
  
describe('Test diffAttributes', function () {
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
describe('Test diffEntity', function () {
    it('Should return false', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var diff1 = {
            "id": "id",
            "typ": "type",
            "attribute": {
                "value": "value",
                "type": "Property"
            }
        }
         
        var diff2 = {
            "id": "id",
            "typ": "type",
            "attribute": {
                "value": "value",
                "type": "Property"
            }
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffEntity(diff1, diff2);
        assert.equal(result, false);
        revert();
    });
    it('Should return true', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var diff1 = {
            "id": "id",
            "typ": "type",
            "attribute": {
                "value": "value",
                "type": "Property"
            }
        }
         
        var diff2 = {
            "id": "id",
            "typ": "type",
            "attribute": {
                "value": "value2",
                "type": "Property"
            }
        }
        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.diffEntity(diff1, diff2);
        assert.equal(result, true);
        revert();
    });
});
describe('Test parseBeforeAfterEntity', function () {
    it('Should return one entity, one Property & one Relationship', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var ba = {
            "id": "id",
            "type": "type",
            "data": "{\
                \"@id\":\"id\", \"@type\": [\"type\"],\
                \"https://uri.etsi.org/ngsi-ld/createdAt\":[{\
                    \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                    \"@value\": \"2022-02-19T20:31:26.123656Z\"\
                }],\
                \"https://example/hasRel\": [{\
                    \"@type\": [\"https://uri.etsi.org/ngsi-ld/Relationship\"],\
                    \"https://uri.etsi.org/ngsi-ld/createdAt\":[{\
                        \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                        \"@value\": \"2022-02-19T20:31:26.123656Z\"\
                    }],\
                    \"https://uri.etsi.org/ngsi-ld/hasObject\": [{\"@id\": \"urn:object:1\"}]\
                }],\
                \"https://example/prop\":[{\
                    \"https://uri.etsi.org/ngsi-ld/hasValue\": [{\"@value\": \"value\"}],\
                    \"https://uri.etsi.org/ngsi-ld/createdAt\":[{\
                        \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                        \"@value\": \"2022-02-19T20:31:26.123656Z\"\
                    }],\
                    \"https://uri.etsi.org/ngsi-ld/modifiedAt\":[{\
                        \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                        \"@value\": \"2022-02-19T23:11:28.457509Z\"\
                    }]\
                }]\
            }"
        }

        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.parseBeforeAfterEntity(ba);
        assert.deepEqual(result.entity,{"id": "id", "type": "type", "https://example/hasRel": "id\\https://example/hasRel", "https://example/prop": "id\\https://example/prop"})
        assert.deepEqual(result.attributes, {
            "https://example/hasRel": [{
                "id": "id\\https://example/hasRel",
                "entityId": "id",
                "synchronized": true,
                "name": "https://example/hasRel",
                "type": "https://uri.etsi.org/ngsi-ld/Relationship",
                "https://uri.etsi.org/ngsi-ld/hasObject": "urn:object:1",
                "index": 0
            }],
            "https://example/prop":[{
                "id": "id\\https://example/prop",
                "entityId": "id",
                "synchronized": true,
                "name": "https://example/prop",
                "type": "https://uri.etsi.org/ngsi-ld/Property",
                "https://uri.etsi.org/ngsi-ld/hasValue": "value",
                "index": 0
            }]
        });
        revert();
    });
    it('Should return one entity, one Property with valuetype', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var ba = {
            "id": "id",
            "type": "type",
            "data": "{\
                \"@id\":\"id\", \"@type\": [\"type\"],\
                \"https://uri.etsi.org/ngsi-ld/createdAt\":[{\
                    \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                    \"@value\": \"2022-02-19T20:31:26.123656Z\"\
                }],\
                \"https://example/prop\":[{\
                    \"https://uri.etsi.org/ngsi-ld/hasValue\": [{\
                        \"@value\": \"value\",\
                        \"@type\": \"https://example/type\"\
                    }],\
                    \"https://uri.etsi.org/ngsi-ld/createdAt\":[{\
                        \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                        \"@value\": \"2022-02-19T20:31:26.123656Z\"\
                    }],\
                    \"https://uri.etsi.org/ngsi-ld/modifiedAt\":[{\
                        \"@type\": \"https://uri.etsi.org/ngsi-ld/DateTime\",\
                        \"@value\": \"2022-02-19T23:11:28.457509Z\"\
                    }]\
                }]\
            }"
        }

        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.parseBeforeAfterEntity(ba);
        assert.deepEqual(result.entity,{"id": "id", "type": "type", "https://example/prop": "id\\https://example/prop"})
        assert.deepEqual(result.attributes, {
            "https://example/prop":[{
                "id": "id\\https://example/prop",
                "entityId": "id",
                "synchronized": true,
                "name": "https://example/prop",
                "type": "https://uri.etsi.org/ngsi-ld/Property",
                "https://uri.etsi.org/ngsi-ld/hasValue": "value",
                "valuetype": "https://example/type",
                "index": 0
            }]
        });
        revert();
    });
    it('Should return `undefined` due to json parse error', async function () {
        var config = {}
        var Logger = function() {
            return logger;
        }
        var ba = {
            "id": "id",
            "type": "type",
            "data": "{\"@id\":\"id\", \"@type\": [\"type\"],"
            }

        var revert = toTest.__set__("Logger", Logger); 
        var debeziumBridge = new toTest(config);
        var result = debeziumBridge.parseBeforeAfterEntity(ba);
        assert.equal(result, undefined);
        revert();
    });
})