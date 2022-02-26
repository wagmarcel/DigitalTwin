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
const { rest } = require('underscore');
const toTest = rewire('../lib/ngsild.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  

describe('Test getNgsildEntity', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            path: '/ngsi-ld/v1/entities/id',
            method: 'GET',
            headers: {
                "Accept": "application/ld+json" 
            }
        }
        const rest = {
            getBody: function(options) {
                assert.deepEqual(options, expectedOptions);
                return "body"
            }
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.getNgsildEntity("id");
        revert();
    });
});
describe('Test getNgsildEntities', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'GET',
            path: "/ngsi-ld/v1/entities?id=urn1,urn2&idPattern=pattern&attrs=attr1,attr2&type=type&q=query1|query2",
            headers: {
                "Accept": "application/ld+json" 
            }
        };
        const rest = {
            getBody: function(options) {
                assert.deepEqual(options, expectedOptions);
                return "body"
            }
        }
        var params = {
            ids: ["urn1", "urn2"],
            idPattern: "pattern",
            attrs: ["attr1", "attr2"],
            type: ["type"],
            queries: ["query1", "query2"]
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.getNgsildEntities(params);
        revert();
    });
});

describe('Test getNgsildCSourceRegistrations', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'GET',
            path: "/ngsi-ld/v1/csourceRegistrations?id=urn1,urn2&idPattern=pattern&attrs=attr1,attr2&type=type",
            headers: {
                "Accept": "application/ld+json",
                "Content-type": "application/ld+json"                 
            }
        };
        const rest = {
            getBody: function(options) {
                assert.deepEqual(options, expectedOptions);
                return "body"
            }
        }
        var params = {
            ids: ["urn1", "urn2"],
            idPattern: "pattern",
            attrs: ["attr1", "attr2"],
            types: ["type"]
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.getNgsildCSourceRegistrations(params);
        revert();
    });
});
describe('Test deleteNgsildCSourceRegistration', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            path: '/ngsi-ld/v1/entities/id',
            method: 'DELETE',
            path: "/ngsi-ld/v1/csourceRegistrations/id"
        };
        const rest = {
            getBody: function(options) {
                assert.deepEqual(options, expectedOptions);
                return "body"
            }
        }

        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.deleteNgsildCSourceRegistration("id");
        revert();
    });
});
describe('Test createNgsildCSourceRegistration', function () {
    it('Should use correct options and used Content-Type ld+json', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            path: '/ngsi-ld/v1/entities/id',
            method: 'POST',
            path: "/ngsi-ld/v1/csourceRegistrations",
            headers: {
                "Content-Type": "application/ld+json"                 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entity);
            }
        }

        const entity = {
            entity: "entity"
        }

        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.createNgsildCSourceRegistration(entity, true);
        revert();
    });
    it('Should use correct options and used Content-Type json', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            path: '/ngsi-ld/v1/entities/id',
            method: 'POST',
            path: "/ngsi-ld/v1/csourceRegistrations",
            headers: {
                "Content-Type": "application/json"                 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entity);
            }
        }

        const entity = {
            entity: "entity"
        }

        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.createNgsildCSourceRegistration(entity, false);
        revert();
    });
});
describe('Test getAllObjectsOfType', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'GET',
            path: "/ngsi-ld/v1/entities?type=type",
            headers: {
                "Accept": "application/ld+json" 
            }
        };
        const rest = {
            getBody: function(options) {
                assert.deepEqual(options, expectedOptions);
                return "body"
            }
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.getAllObjectsOfType("type");
        result.should.equal("body");
        revert();
    });
});
describe('Test deleteEntities', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entityOperations/delete"
,
            headers: {
                "Content-Type": "application/json" 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, ids);
                return "deleted"
            }
        }
        const ids = ["id1", "id2"];
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.deleteEntities(ids);
        result.should.equal("deleted");
        revert();
    });
});
describe('Test createEntities', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entityOperations/create",
            headers: {
                "Content-Type": "application/ld+json"                 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entities);
                return "created";
            }
        }

        const entities = [
        {
            entity: "entity"
        },
        {
            entity: "entity2"
        },
    ]

        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.createEntities(entities);
        result.should.equal("created");
        revert();
    });
});
describe('Test replaceEntities', function () {
    it('Should use correct options', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entityOperations/upsert",
            headers: {
                "Content-Type": "application/ld+json",
                "header": "header"                 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entities);
                return "replaced";
            }
        }

        const entities = [
            {
                entity: "entity"
            },
            {
                entity: "entity2"
            },
        ]
        const headers = {
            "header": "header"
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.replaceEntities(entities, false, {headers});
        result.should.equal("replaced");
        revert();
    });
    it('Should use correct options and add ?option=update to path', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entityOperations/upsert?options=update",
            headers: {
                "Content-Type": "application/ld+json",
                "header": "header"                 
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entities);
                return "replaced";
            }
        }

        const entities = [
            {
                entity: "entity"
            },
            {
                entity: "entity2"
            },
        ]
        const headers = {
            "header": "header"
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.replaceEntities(entities, true, {headers});
        result.should.equal("replaced");
        revert();
    });
});
describe('Test updateProperties', function () {
    it('Should use correct options ', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entities/id/attrs?options=noOverwrite",
            headers: {
                "Content-Type": "application/json",
                "header": "header"
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entity);
                assert.equal(obj.disableChunks, false);
                assert.equal(obj.noStringify, true);
                return "updated";
            }
        }

        const entity = {
            entity: "entity"
        }
        const headers = {
            "header": "header"
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.updateProperties("id", entity, true, {headers});
        result.should.equal("updated");
        revert();
    });
    it('Should use correct options and not use noOverwrite', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/entities/id/attrs",
            headers: {
                "Content-Type": "application/json",
                "header": "header"
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entity);
                assert.equal(obj.disableChunks, false);
                assert.equal(obj.noStringify, true);
                return "updated";
            }
        }

        const entity = {
            entity: "entity"
        }
        const headers = {
            "header": "header"
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.updateProperties("id", entity, false, {headers});
        result.should.equal("updated");
        revert();
    });
});
describe('Test subscribe', function () {
    it('Should use correct options ', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            },
            bridgeConfig: {
                host: "host",
                port: 123
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }

        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            method: 'POST',
            path: "/ngsi-ld/v1/subscriptions/",
            headers: {
                "Content-Type": "application/ld+json"
            }
        };
        const rest = {
            postBody: function(obj) {
                assert.deepEqual(obj.options, expectedOptions);
                assert.deepEqual(obj.body, entity);
                return "subscribed";
            }
        }

        const entity = {
            "@context": [
                "https://fiware.github.io/data-models/context.jsonld",
                "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.3.jsonld",
                "host:123/jsonld/undefined"
            ],
            description: "Notify me if type are changed",
            entities: [
                {
                    type: "http://example/type"
                }
            ],
            id: "id",
            notification: {
                endpoint: {
                    accept: "application/json",
                    uri: "host:123/subscription"
                }
            },
            timeInterval: 200,
            type: "Subscription"
        }
      
        const headers = {
            "header": "header"
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("Rest", Rest);
        var ngsild = new toTest(config);
        var result = ngsild.subscribe("id", "http://example/type", 200);
        result.should.equal("subscribed");
        revert();
    });
});