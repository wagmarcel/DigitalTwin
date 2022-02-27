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
const toTest = rewire('../lib/ngsildUpdates.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  

describe('Test libNgsildUpdates', function () {
    it('Should post body with correct path and token for nonOverwrite update', async function () {

        var config = {
            ngsildUpdates: {
                clientSecretVariable: "CLIENT_SECRET",
                refreshIntervalInSeconds: 200
            },
            keycloak: {
                ngsildUpdatesAuthService: {

                }
            }
        }
        var Logger = function() {
            return logger;
        }
        var process = {
            env: {
                "CLIENT_SECRET": "client_secret"
            }
        }
        var body = {
            "op":  "update",
            "entity": "entity",
            "id": "id",
            "overwrite": false
        }
        var expHeaders = {
            "Authorization": "Bearer token"
        }
        const Ngsild = function(){
            return {
                updateProperties: function(id, entity, noOverwrite, {headers}) {
                    id.should.equal("id");
                    entity.should.equal("entity");
                    noOverwrite.should.equal(true);
                    assert.deepEqual(headers, expHeaders);
                    return {
                        statusCode: 204
                    }
                },
                replaceEntities: function(){
                }
            }
        }
        const setInterval = function(fun, interv){
        }
        const Keycloak = function(){
            return {
                grantManager: {
                    obtainFromClientCredentials: async function() {
                        return new Promise(function(resolve, reject){
                            resolve({
                                access_token: {
                                    token: "token"
                                }
                            })
                        })
                    }
                }
            }
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("process", process);
        toTest.__set__("NgsiLd", Ngsild);
        toTest.__set__("setInterval", setInterval);
        toTest.__set__("Keycloak", Keycloak);
        var ngsildUpdates = new toTest(config);
        var result = await ngsildUpdates.ngsildUpdates(body);
        revert();
    });
    it('Should post body with correct path and token for nonOverwrite upsert', async function () {

        var config = {
            ngsildUpdates: {
                clientSecretVariable: "CLIENT_SECRET",
                refreshIntervalInSeconds: 200
            },
            keycloak: {
                ngsildUpdatesAuthService: {

                }
            }
        }
        var Logger = function() {
            return logger;
        }
        var process = {
            env: {
                "CLIENT_SECRET": "client_secret"
            }
        }
        var body = {
            "op":  "upsert",
            "entity": "entity",
            "id": "id",
            "overwrite": false
        }
        var expHeaders = {
            "Authorization": "Bearer token"
        }
        const Ngsild = function(){
            return {
                replaceEntities: function([entity], noOverwrite, {headers}) {
                    entity.should.equal("entity");
                    noOverwrite.should.equal(true);
                    assert.deepEqual(headers, expHeaders);
                    return {
                        statusCode: 204
                    }
                }
            }
        }
        const setInterval = function(fun, interv){
        }
        const Keycloak = function(){
            return {
                grantManager: {
                    obtainFromClientCredentials: async function() {
                        return new Promise(function(resolve, reject){
                            resolve({
                                access_token: {
                                    token: "token"
                                }
                            })
                        })
                    }
                }
            }
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("process", process);
        toTest.__set__("NgsiLd", Ngsild);
        toTest.__set__("setInterval", setInterval);
        toTest.__set__("Keycloak", Keycloak);
        var ngsildUpdates = new toTest(config);
        var result = await ngsildUpdates.ngsildUpdates(body);
        revert();
    });
});