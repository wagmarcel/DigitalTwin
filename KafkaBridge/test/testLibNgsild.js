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
    it('Should get body with correct path and token', async function () {

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
    it('Should get body with correct path and token', async function () {

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
    it('Should get body with correct path and token', async function () {

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